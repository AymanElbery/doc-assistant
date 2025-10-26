import { Component, signal, inject, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService, ChatSource } from '../../core/services/api.service';
import { KeycloakService } from '../../core/services/keycloak.service';

// Update Message interface
interface Message {
    role: 'user' | 'assistant';
    content: string;
    sources?: ChatSource[];
    timestamp: Date;
    maxRelevanceScore?: number;
    isNoAnswer?: boolean;
}
@Component({
    selector: 'app-chat',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './chat.component.html',
    styleUrls: ['./chat.component.css']
})
export class ChatComponent implements AfterViewChecked {
    // ... (keep existing properties and interfaces)
    @ViewChild('messagesContainer') private messagesContainer!: ElementRef;

    private apiService = inject(ApiService);
    private keycloakService = inject(KeycloakService);
    private router = inject(Router);
  
    messages = signal<Message[]>([]);
    inputMessage = '';
    isTyping = signal(false);
    selectedSource = signal<ChatSource | null>(null);
    username = signal('');
    private shouldScrollToBottom = false;

    ngOnInit() {
        this.username.set(this.keycloakService.getUsername());
    }

    ngAfterViewChecked() {
        if (this.shouldScrollToBottom) {
        this.scrollToBottom();
        this.shouldScrollToBottom = false;
        }
    }

    sendMessage(event: Event) {
        event.preventDefault();
        
        const message = this.inputMessage.trim();
        if (!message || this.isTyping()) return;
    
        // Add user message
        this.messages.update(msgs => [...msgs, {
          role: 'user',
          content: message,
          timestamp: new Date()
        }]);
    
        this.inputMessage = '';
        this.isTyping.set(true);
        this.shouldScrollToBottom = true;
    
        // Stream response
        this.streamChatResponse(message);
    }

    private streamChatResponse(message: string) {
        this.apiService.chatStream(message).subscribe({
            next: (response) => {
                this.handleStreamResponse(response);
            },
            error: (error) => {
                this.isTyping.set(false);
                this.messages.update(msgs => [...msgs, {
                    role: 'assistant',
                    content: 'Sorry, I encountered an error processing your request. Please make sure you have uploaded documents first.',
                    timestamp: new Date()
                }]);
                this.shouldScrollToBottom = true;
            }
        });
    }
    
    private handleStreamResponse(streamText: string) {
        const lines = streamText.split('\n');
        let assistantMessage: Message | null = null;
        let sources: ChatSource[] = [];
        let accumulatedText = '';
        let maxScore = 0;
        let isNoAnswer = false;

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = line.substring(6);

                if (data === '[DONE]') {
                    if (assistantMessage) {
                        assistantMessage.content = accumulatedText.trim();
                        assistantMessage.sources = sources;
                        assistantMessage.maxRelevanceScore = maxScore;
                        assistantMessage.isNoAnswer = isNoAnswer;
                    }
                    this.isTyping.set(false);
                    continue;
                }

                try {
                    const parsed = JSON.parse(data);

                    if (parsed.type === 'sources') {
                        sources = parsed.data;
                        maxScore = parsed.max_score || (sources.length > 0 ? Math.max(...sources.map((s: any) => s.score)) : 0);
                        assistantMessage = {
                            role: 'assistant',
                            content: '',
                            sources: sources,
                            timestamp: new Date(),
                            maxRelevanceScore: maxScore,
                            isNoAnswer: false
                        };
                        this.messages.update(msgs => [...msgs, assistantMessage!]);
                        this.shouldScrollToBottom = true;
                    } else if (parsed.type === 'no_answer') {
                        isNoAnswer = true;
                        accumulatedText = parsed.data;
                        maxScore = parsed.max_score || 0;
                        if (assistantMessage) {
                            assistantMessage.isNoAnswer = true;
                            assistantMessage.maxRelevanceScore = maxScore;
                            this.messages.update(msgs => {
                                const newMsgs = [...msgs];
                                newMsgs[newMsgs.length - 1] = {
                                    ...assistantMessage!,
                                    content: accumulatedText,
                                    isNoAnswer: true,
                                    maxRelevanceScore: maxScore
                                };
                                return newMsgs;
                            });
                        }
                        this.isTyping.set(false);
                        this.shouldScrollToBottom = true;
                    } else if (parsed.type === 'token') {
                        accumulatedText += parsed.data;
                        if (assistantMessage) {
                            this.messages.update(msgs => {
                                const newMsgs = [...msgs];
                                newMsgs[newMsgs.length - 1] = {
                                    ...assistantMessage!,
                                    content: accumulatedText
                                };
                                return newMsgs;
                            });
                            this.shouldScrollToBottom = true;
                        }
                    }
                } catch (e) {
                    // Ignore JSON parse errors
                }
            }
        }
    }

    selectSource(source: ChatSource) {
        this.selectedSource.set(source);
    }

    formatTime(date: Date): string {
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    scrollToBottom(): void {
        try {
            this.messagesContainer.nativeElement.scrollTop =
                this.messagesContainer.nativeElement.scrollHeight;
        } catch (err) { }
    }

    navigateToUpload() {
        this.router.navigate(['/upload']);
    }

    logout() {
        this.keycloakService.logout();
    }
}


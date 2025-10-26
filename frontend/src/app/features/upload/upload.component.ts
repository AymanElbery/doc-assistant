import { Component, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { KeycloakService } from '../../core/services/keycloak.service';

@Component({
    selector: 'app-upload',
    standalone: true,
    imports: [CommonModule],
    templateUrl: './upload.component.html',
    styleUrls: ['./upload.component.css']
})
export class UploadComponent {
    private apiService = inject(ApiService);
    private keycloakService = inject(KeycloakService);
    private router = inject(Router);

    selectedFile = signal<File | null>(null);
    uploading = signal(false);
    uploadProgress = signal<number | null>(null);
    uploadStatus = signal<{ type: 'success' | 'error', message: string } | null>(null);

    documents = signal<any[]>([]);
    loading = signal(false);

    username = signal('');

    ngOnInit() {
        this.username.set(this.keycloakService.getUsername());
        this.loadDocuments();
    }

    onFileSelected(event: Event) {
        const input = event.target as HTMLInputElement;
        if (input.files && input.files.length > 0) {
            this.selectedFile.set(input.files[0]);
            this.uploadStatus.set(null);
        }
    }

    async uploadFile() {
        const file = this.selectedFile();
        if (!file) return;

        this.uploading.set(true);
        this.uploadProgress.set(0);
        this.uploadStatus.set(null);

        // Simulate progress
        const progressInterval = setInterval(() => {
            const current = this.uploadProgress() || 0;
            if (current < 90) {
                this.uploadProgress.set(current + 10);
            }
        }, 200);

        this.apiService.uploadDocument(file).subscribe({
            next: (response) => {
                clearInterval(progressInterval);
                this.uploadProgress.set(100);
                this.uploadStatus.set({
                    type: 'success',
                    message: `Successfully uploaded! Processed ${response.chunks_processed} chunks.`
                });
                this.selectedFile.set(null);
                this.loadDocuments();

                setTimeout(() => {
                    this.uploading.set(false);
                    this.uploadProgress.set(null);
                }, 1000);
            },
            error: (error) => {
                clearInterval(progressInterval);
                this.uploading.set(false);
                this.uploadProgress.set(null);
                this.uploadStatus.set({
                    type: 'error',
                    message: error.error?.detail || 'Upload failed. Please try again.'
                });
            }
        });
    }

    loadDocuments() {
        this.loading.set(true);
        this.apiService.listDocuments().subscribe({
            next: (response) => {
                this.documents.set(response.documents);
                this.loading.set(false);
            },
            error: (error) => {
                console.error('Failed to load documents', error);
                this.loading.set(false);
            }
        });
    }

    formatFileSize(bytes: number): string {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    navigateToChat() {
        this.router.navigate(['/chat']);
    }

    logout() {
        this.keycloakService.logout();
    }
}
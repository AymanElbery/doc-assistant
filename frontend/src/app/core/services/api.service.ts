import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environment/environment';

export interface UploadResponse {
  filename: string;
  chunks_processed: number;
  status: string;
}

export interface ChatRequest {
  message: string;
  stream: boolean;
}

export interface ChatSource {
  filename: string;
  page: number | string;
  text: string;
  score: number;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;

  uploadDocument(file: File): Observable<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post<UploadResponse>(
      `${this.apiUrl}/documents/upload`,
      formData
    );
  }

  listDocuments(): Observable<{ documents: any[] }> {
    return this.http.get<{ documents: any[] }>(
      `${this.apiUrl}/documents/documents`
    );
  }

  chatStream(message: string): Observable<string> {
    return this.http.post(
      `${this.apiUrl}/chat/chat`,
      { message, stream: true },
      { 
        observe: 'body',
        responseType: 'text'
      }
    );
  }

  chatNonStream(message: string): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(
      `${this.apiUrl}/chat/chat`,
      { message, stream: false },
      { 
        observe: 'body',
        responseType: 'json'
      }
    );
  }
}
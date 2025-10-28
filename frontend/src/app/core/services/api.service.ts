import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environment/environment';
import { KeycloakService } from './keycloak.service';

export interface UploadResponse {
  filename: string;
  chunks_processed: number;
  status: string;
  user_id: string;
}

export interface DeleteResponse {
  filename: string;
  status: string;
  vectors_deleted: number;
  message: string;
}

export interface DeleteAllResponse {
  status: string;
  files_deleted: number;
  vectors_deleted: number;
  message: string;
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
  private keycloakService = inject(KeycloakService);
  private apiUrl = environment.apiUrl;

  uploadDocument(file: File): Observable<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post<UploadResponse>(
      `${this.apiUrl}/documents/upload`,
      formData
    );
  }

  listDocuments(): Observable<{ documents: any[]; count: number }> {
    return this.http.get<{ documents: any[]; count: number }>(
      `${this.apiUrl}/documents/documents`
    );
  }

  deleteDocument(filename: string): Observable<DeleteResponse> {
    return this.http.delete<DeleteResponse>(
      `${this.apiUrl}/documents/documents/${encodeURIComponent(filename)}`
    );
  }

  deleteAllDocuments(): Observable<DeleteAllResponse> {
    return this.http.delete<DeleteAllResponse>(
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
      { message, stream: false }
    );
  }

  getDocumentUrl(filename: string, page: number | string): string {
    const token = this.keycloakService.getToken();
    const baseUrl = `${this.apiUrl}/documents/view/${encodeURIComponent(filename)}`;
    const urlWithParams = `${baseUrl}?page=${page}${token ? `&token=${token}` : ''}`;
    return urlWithParams;
  }
}
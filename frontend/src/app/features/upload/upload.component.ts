import { Component, signal, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { KeycloakService } from '../../core/services/keycloak.service';
import Swal from 'sweetalert2';

interface Document {
  filename: string;
  size: number;
  uploaded_at: number;
  extension: string;
  vector_count?: number;
}

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './upload.component.html',  
  styleUrls: ['./upload.component.css']
})
export class UploadComponent implements OnInit {
  private apiService = inject(ApiService);
  private keycloakService = inject(KeycloakService);
  private router = inject(Router);

  username = signal('');
  documents = signal<Document[]>([]);
  loading = signal(false);
  isDragging = signal(false);
  uploadProgress = signal(0);
  uploadError = signal('');
  uploadSuccess = signal('');
  deletingFile = signal<string | null>(null);

  ngOnInit() {
    this.username.set(this.keycloakService.getUsername());
    this.loadDocuments();
  }

  loadDocuments() {
    this.loading.set(true);
    this.apiService.listDocuments().subscribe({
      next: (response) => {
        this.documents.set(response.documents);
        this.loading.set(false);
      },
      error: (error) => {
        console.error('Error loading documents:', error);
        this.loading.set(false);
        Swal.fire({
          icon: 'error',
          title: 'Error',
          text: 'Failed to load documents. Please try again.',
          confirmButtonColor: '#6366f1'
        });
      }
    });
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.uploadFile(input.files[0]);
    }
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    this.isDragging.set(true);
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    this.isDragging.set(false);
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    this.isDragging.set(false);
    
    if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
      this.uploadFile(event.dataTransfer.files[0]);
    }
  }

  uploadFile(file: File) {
    this.uploadProgress.set(0);
    this.uploadError.set('');
    this.uploadSuccess.set('');

    // Validate file type
    const allowedTypes = ['.pdf', '.docx', '.xlsx'];
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedTypes.includes(fileExt)) {
      Swal.fire({
        icon: 'error',
        title: 'Invalid File Type',
        text: 'Only PDF, DOCX, and XLSX files are allowed.',
        confirmButtonColor: '#6366f1'
      });
      return;
    }

    // Validate file size (50MB)
    if (file.size > 50 * 1024 * 1024) {
      Swal.fire({
        icon: 'error',
        title: 'File Too Large',
        text: 'Maximum file size is 50MB.',
        confirmButtonColor: '#6366f1'
      });
      return;
    }

    this.uploadProgress.set(10);

    this.apiService.uploadDocument(file).subscribe({
      next: (response) => {
        this.uploadProgress.set(100);
        
        Swal.fire({
          icon: 'success',
          title: 'Upload Successful!',
          html: `
            <div class="text-left">
              <p class="mb-2"><strong>File:</strong> ${response.filename}</p>
              <p class="mb-2"><strong>Chunks Processed:</strong> ${response.chunks_processed}</p>
              <p class="text-sm text-gray-600">Your document is now ready for questions!</p>
            </div>
          `,
          confirmButtonColor: '#6366f1',
          timer: 3000,
          timerProgressBar: true
        });
        
        setTimeout(() => {
          this.uploadProgress.set(0);
        }, 1000);
        
        this.loadDocuments();
      },
      error: (error) => {
        this.uploadProgress.set(0);
        
        Swal.fire({
          icon: 'error',
          title: 'Upload Failed',
          text: error.error?.detail || 'Failed to upload document. Please try again.',
          confirmButtonColor: '#6366f1'
        });
      }
    });
  }

  async deleteDocument(doc: Document) {
    const result = await Swal.fire({
      title: 'Delete Document?',
      html: `
        <div class="text-left">
          <p class="mb-3">Are you sure you want to delete this document?</p>
          <div class="bg-gray-50 p-3 rounded-lg mb-3">
            <p class="font-medium text-gray-900 mb-1">${doc.filename}</p>
            <p class="text-sm text-gray-600">Size: ${this.formatFileSize(doc.size)}</p>
            ${doc.vector_count ? `<p class="text-sm text-gray-600">Vectors: ${doc.vector_count}</p>` : ''}
          </div>
          <p class="text-sm text-red-600">⚠️ This will permanently delete the file and all associated vectors from the database.</p>
        </div>
      `,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#ef4444',
      cancelButtonColor: '#6b7280',
      confirmButtonText: 'Yes, delete it!',
      cancelButtonText: 'Cancel',
      reverseButtons: true
    });

    if (result.isConfirmed) {
      this.deletingFile.set(doc.filename);

      this.apiService.deleteDocument(doc.filename).subscribe({
        next: (response) => {
          this.deletingFile.set(null);
          
          Swal.fire({
            icon: 'success',
            title: 'Deleted!',
            html: `
              <div class="text-left">
                <p class="mb-2">Successfully deleted <strong>${doc.filename}</strong></p>
                <p class="text-sm text-gray-600">${response.vectors_deleted} vectors removed from database</p>
              </div>
            `,
            confirmButtonColor: '#6366f1',
            timer: 2000,
            timerProgressBar: true
          });
          
          this.loadDocuments();
        },
        error: (error) => {
          this.deletingFile.set(null);
          
          Swal.fire({
            icon: 'error',
            title: 'Delete Failed',
            text: error.error?.detail || 'Failed to delete document. Please try again.',
            confirmButtonColor: '#6366f1'
          });
        }
      });
    }
  }

  async deleteAllDocuments() {
    const documentCount = this.documents().length;
    const totalVectors = this.documents().reduce((sum, doc) => sum + (doc.vector_count || 0), 0);

    const result = await Swal.fire({
      title: 'Delete All Documents?',
      html: `
        <div class="text-left">
          <p class="mb-3">This will permanently delete:</p>
          <div class="bg-red-50 p-4 rounded-lg mb-3 border border-red-200">
            <p class="font-bold text-red-900 mb-2">⚠️ WARNING: This action cannot be undone!</p>
            <ul class="list-disc list-inside space-y-1 text-sm text-red-800">
              <li><strong>${documentCount}</strong> document${documentCount !== 1 ? 's' : ''}</li>
              <li><strong>${totalVectors}</strong> vector${totalVectors !== 1 ? 's' : ''} from database</li>
            </ul>
          </div>
          <p class="text-sm text-gray-700">Type <strong>DELETE</strong> to confirm:</p>
        </div>
      `,
      icon: 'warning',
      input: 'text',
      inputPlaceholder: 'Type DELETE to confirm',
      showCancelButton: true,
      confirmButtonColor: '#ef4444',
      cancelButtonColor: '#6b7280',
      confirmButtonText: 'Delete Everything',
      cancelButtonText: 'Cancel',
      reverseButtons: true,
      inputValidator: (value) => {
        if (value !== 'DELETE') {
          return 'You must type DELETE to confirm!';
        }
        return null;
      }
    });

    if (result.isConfirmed) {
      // Show loading
      Swal.fire({
        title: 'Deleting...',
        html: 'Please wait while we delete all documents and vectors.',
        allowOutsideClick: false,
        didOpen: () => {
          Swal.showLoading();
        }
      });

      this.apiService.deleteAllDocuments().subscribe({
        next: (response) => {
          Swal.fire({
            icon: 'success',
            title: 'All Documents Deleted!',
            html: `
              <div class="text-left">
                <p class="mb-3">Successfully deleted all your documents:</p>
                <div class="bg-green-50 p-3 rounded-lg">
                  <p class="text-sm text-green-800">📄 ${response.files_deleted} file${response.files_deleted !== 1 ? 's' : ''} deleted</p>
                  <p class="text-sm text-green-800">🗄️ ${response.vectors_deleted} vector${response.vectors_deleted !== 1 ? 's' : ''} removed</p>
                </div>
              </div>
            `,
            confirmButtonColor: '#6366f1',
            timer: 3000,
            timerProgressBar: true
          });
          
          this.loadDocuments();
        },
        error: (error) => {
          Swal.fire({
            icon: 'error',
            title: 'Delete Failed',
            text: error.error?.detail || 'Failed to delete documents. Please try again.',
            confirmButtonColor: '#6366f1'
          });
        }
      });
    }
  }

  formatFileSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  formatDate(timestamp: number): string {
    return new Date(timestamp * 1000).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  navigateToChat() {
    this.router.navigate(['/chat']);
  }

  logout() {
    this.keycloakService.logout();
  }
}
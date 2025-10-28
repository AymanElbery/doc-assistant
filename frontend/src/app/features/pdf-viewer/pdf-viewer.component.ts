import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { ApiService } from '../../core/services/api.service';
import { KeycloakService } from '../../core/services/keycloak.service';

@Component({
    selector: 'app-pdf-viewer',
    standalone: true,
    imports: [CommonModule],
    templateUrl: './pdf-viewer.component.html',
    styleUrls: ['./pdf-viewer.component.css']
})
export class PdfViewerComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private sanitizer = inject(DomSanitizer);
  private apiService = inject(ApiService);
  private keycloakService = inject(KeycloakService);

  filename = signal<string>('');
  page = signal<string | number>('');
  fileExtension = signal<string>('');
  pdfUrl = signal<SafeResourceUrl | null>(null);
  loading = signal(true);
  error = signal<string>('');
  username = signal<string>('');

  ngOnInit() {
    this.username.set(this.keycloakService.getUsername());

    this.route.queryParams.subscribe((params) => {
      const filename = params['file'];
      const page = params['page'] || 1;

      if (!filename) {
        this.error.set('No file specified');
        this.loading.set(false);
        return;
      }

      this.filename.set(decodeURIComponent(filename));
      this.page.set(page);

      const ext = this.getFileExtension(filename);
      this.fileExtension.set(ext);

      this.loadDocument(filename, page);
    });
  }

  loadDocument(filename: string, page: string | number) {
    this.loading.set(true);
    this.error.set('');
  
    const ext = this.getFileExtension(filename);
  
    if (ext === 'pdf') {
      // For PDFs, use direct embedding
      const baseUrl = this.apiService.getDocumentUrl(filename, page);
      const pdfUrlWithPage = `${baseUrl}#page=${page}`;
      this.pdfUrl.set(this.sanitizer.bypassSecurityTrustResourceUrl(pdfUrlWithPage));
      this.loading.set(false);
    } else if (ext === 'docx' || ext === 'xlsx') {
      // For Office documents, use Google Docs Viewer
      const baseUrl = this.apiService.getDocumentUrl(filename, page);
      const encodedUrl = encodeURIComponent(baseUrl);
      const googleViewerUrl = `https://docs.google.com/viewer?url=${encodedUrl}&embedded=true`;
      this.pdfUrl.set(this.sanitizer.bypassSecurityTrustResourceUrl(googleViewerUrl));
      this.loading.set(false);
    } else {
      this.loading.set(false);
    }
  }

  isOfficeDocument(): boolean {
    const ext = this.fileExtension();
    return ext === 'docx' || ext === 'xlsx' || ext === 'doc' || ext === 'xls';
  }

  getFileExtension(filename: string): string {
    return filename.split('.').pop()?.toLowerCase() || '';
  }

  downloadDocument() {
    const filename = this.filename();
    const page = this.page();
    const url = this.apiService.getDocumentUrl(filename, page);

    // Create a temporary link and click it to trigger download
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  goBack() {
    this.router.navigate(['/chat']);
  }
}

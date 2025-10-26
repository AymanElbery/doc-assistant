import { Component, inject, OnInit } from '@angular/core';
import { Router, RouterOutlet } from '@angular/router';
import { KeycloakService } from './core/services/keycloak.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent implements OnInit {
  private keycloakService = inject(KeycloakService);
  private router = inject(Router);
  initialized = false;

  async ngOnInit() {
    try {
      console.log('Initializing Keycloak...');
      const authenticated = await this.keycloakService.init();
      console.log('Keycloak initialized. Authenticated:', authenticated);

      this.initialized = true;

      // Navigate based on authentication status
      if (authenticated) {
        // User is authenticated, navigate to chat
        const currentUrl = window.location.href;

        // If we're on the callback URL, navigate to chat
        if (currentUrl.includes('state=') || currentUrl.includes('code=')) {
          console.log('Callback detected, navigating to chat...');
          this.router.navigate(['/chat'], { replaceUrl: true });
        }
      } else {
        // User is not authenticated, stay on current route
        console.log('User not authenticated');
      }
    } catch (error) {
      console.error('Keycloak initialization failed:', error);
      this.initialized = true;
    }
  }
}

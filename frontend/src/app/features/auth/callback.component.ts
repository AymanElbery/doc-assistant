import { Component, inject, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { KeycloakService } from '../../core/services/keycloak.service';

@Component({
    selector: 'app-callback',
    standalone: true,
    templateUrl: './callback.component.html',
    styleUrls: ['./callback.component.css']
})
export class CallbackComponent implements OnInit {
    private router = inject(Router);
    private keycloakService = inject(KeycloakService);

    async ngOnInit() {
        // Wait for Keycloak initialization
        await this.keycloakService.init();

        if (this.keycloakService.isAuthenticated()) {
            this.router.navigate(['/chat']);
        } else {
            this.router.navigate(['/']);
        }
    }
}
import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { KeycloakService } from '../services/keycloak.service';

export const authGuard: CanActivateFn = async (route, state) => {
    const keycloakService = inject(KeycloakService);
    const router = inject(Router);

    console.log('Auth guard checking...', state.url);

    // Wait for initialization if needed
    await keycloakService.init();

    const isAuthenticated = keycloakService.isAuthenticated();
    console.log('Is authenticated:', isAuthenticated);

    if (!isAuthenticated) {
        console.log('Not authenticated, redirecting to login...');
        await keycloakService.login();
        return false;
    }

    return true;
};
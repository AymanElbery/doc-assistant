import { Injectable } from '@angular/core';
import Keycloak from 'keycloak-js';
import { environment } from '../../../environment/environment';

@Injectable({
    providedIn: 'root'
})
export class KeycloakService {
    private keycloak: Keycloak | undefined;
    private isInitialized = false;
    private initPromise: Promise<boolean> | null = null;

    async init(): Promise<boolean> {
        // Prevent multiple initializations
        if (this.isInitialized) {
            console.log('Keycloak already initialized');
            return this.keycloak?.authenticated || false;
        }

        // Return existing promise if initialization is in progress
        if (this.initPromise) {
            console.log('Keycloak initialization in progress...');
            return this.initPromise;
        }

        console.log('Starting Keycloak initialization...');

        this.keycloak = new Keycloak({
            url: environment.keycloak.url,
            realm: environment.keycloak.realm,
            clientId: environment.keycloak.clientId,
        });

        this.initPromise = this.keycloak.init({
            onLoad: 'check-sso',
            silentCheckSsoRedirectUri: window.location.origin + '/assets/silent-check-sso.html',
            pkceMethod: 'S256',
            checkLoginIframe: false, // Disable iframe check to prevent issues
            flow: 'standard'
        }).then((authenticated) => {
            console.log('Keycloak init completed. Authenticated:', authenticated);
            this.isInitialized = true;
            this.initPromise = null;

            // Token refresh setup
            if (authenticated) {
                console.log('Setting up token refresh...');
                this.setupTokenRefresh();
            }

            return authenticated;
        }).catch((error) => {
            console.error('Keycloak initialization error:', error);
            this.isInitialized = true;
            this.initPromise = null;
            return false;
        });

        return this.initPromise;
    }

    private setupTokenRefresh() {
        if (!this.keycloak) return;

        // Refresh token every 60 seconds if it expires in less than 70 seconds
        setInterval(() => {
            this.keycloak?.updateToken(70)
                .then((refreshed) => {
                    if (refreshed) {
                        console.log('Token refreshed');
                    }
                })
                .catch(() => {
                    console.error('Failed to refresh token');
                    this.logout();
                });
        }, 60000);
    }

    login(): Promise<void> {
        if (!this.keycloak) {
            console.error('Keycloak not initialized');
            return Promise.resolve();
        }

        return this.keycloak.login({
            redirectUri: window.location.origin + '/chat'
        });
    }

    logout(): Promise<void> {
        if (!this.keycloak) {
            return Promise.resolve();
        }

        return this.keycloak.logout({
            redirectUri: window.location.origin
        });
    }

    getToken(): string | undefined {
        return this.keycloak?.token;
    }

    isAuthenticated(): boolean {
        return this.keycloak?.authenticated || false;
    }

    getUserProfile() {
        return this.keycloak?.loadUserProfile();
    }

    getUsername(): string {
        return this.keycloak?.tokenParsed?.['preferred_username'] || '';
    }

    getUserId(): string {
        return this.keycloak?.tokenParsed?.['sub'] || '';
    }
}
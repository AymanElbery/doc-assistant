import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
    {
      path: '',
      loadComponent: () => import('./features/landing/landing.component').then(m => m.LandingComponent)
    },
    {
      path: 'home',
      redirectTo: '',
      pathMatch: 'full'
    },
    // {
    //   path: 'auth',
    //   loadChildren: () => import('./features/auth/auth.routes').then(m => m.AUTH_ROUTES)
    // },
    {
      path: 'upload',
      loadComponent: () => import('./features/upload/upload.component').then(m => m.UploadComponent),
      canActivate: [authGuard]
    },
    {
      path: 'chat',
      loadComponent: () => import('./features/chat/chat.component').then(m => m.ChatComponent),
      canActivate: [authGuard]
    },
    {
      path: '**',
      redirectTo: ''
    }
];

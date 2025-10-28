import { Component } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [],
  templateUrl: './landing.component.html',
  styleUrls: ['./landing.component.css']
})
export class LandingComponent {
  constructor(private router: Router) {}

  navigateToChat() {
    this.router.navigate(['/chat']);
  }

  navigateToUpload() {
    this.router.navigate(['/upload']);
  }
}

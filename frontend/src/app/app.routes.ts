import { Routes } from '@angular/router';
import { HomeComponent } from './home/home.component';
import { GameComponent } from './game/game.component';
import { TrainingComponent } from './training/training.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'game', component: GameComponent },
  { path: 'training', component: TrainingComponent },
  { path: '**', redirectTo: '' },
];

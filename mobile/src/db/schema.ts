/**
 * FitBuddy Offline-First Schema Definition (WatermelonDB / SQLite)
 * Enables complete workout tracking, set logging, and offline synchronization in dead zones.
 */

import { appSchema, tableSchema } from '@nozbe/watermelondb';

export const fitbuddySchema = appSchema({
  version: 1,
  tables: [
    tableSchema({
      name: 'users',
      columns: [
        { name: 'user_id', type: 'string', isIndexed: true },
        { name: 'name', type: 'string' },
        { name: 'age', type: 'number' },
        { name: 'weight', type: 'number' },
        { name: 'fitness_goal', type: 'string' },
        { name: 'intensity', type: 'string' },
        { name: 'created_at', type: 'number' },
      ],
    }),
    tableSchema({
      name: 'workout_plans',
      columns: [
        { name: 'user_id', type: 'string', isIndexed: true },
        { name: 'original_plan', type: 'string' },
        { name: 'nutrition_tip', type: 'string', isOptional: true },
        { name: 'updated_plan', type: 'string', isOptional: true },
        { name: 'feedback', type: 'string', isOptional: true },
        { name: 'is_synced', type: 'boolean' },
        { name: 'created_at', type: 'number' },
        { name: 'updated_at', type: 'number', isOptional: true },
      ],
    }),
    tableSchema({
      name: 'logged_sets',
      columns: [
        { name: 'plan_id', type: 'string', isIndexed: true },
        { name: 'exercise_name', type: 'string' },
        { name: 'set_number', type: 'number' },
        { name: 'weight_kg', type: 'number' },
        { name: 'reps_completed', type: 'number' },
        { name: 'rpe', type: 'number', isOptional: true },
        { name: 'is_synced', type: 'boolean' },
        { name: 'created_at', type: 'number' },
      ],
    }),
  ],
});

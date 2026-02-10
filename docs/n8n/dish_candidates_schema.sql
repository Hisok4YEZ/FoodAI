create table if not exists public.dish_candidates (
  id uuid default gen_random_uuid() primary key,
  dish_name text not null,
  source_keyword text,
  servings integer default 2,
  image_url text,
  notes text,
  recipe_payload jsonb,
  is_new_dish boolean not null default true,
  status text not null default 'pending',
  added_to_training boolean not null default false,
  admin_note text,
  created_at timestamptz default now()
);

create index if not exists idx_dish_candidates_created_at
  on public.dish_candidates(created_at desc);

create index if not exists idx_dish_candidates_status
  on public.dish_candidates(status);

alter table public.dish_candidates enable row level security;

drop policy if exists "Admin only dish candidates" on public.dish_candidates;
create policy "Admin only dish candidates"
  on public.dish_candidates
  using (false)
  with check (false);

-- Les écritures/lectures passent par le backend (service role / admin token),
-- pas directement depuis le client Supabase.

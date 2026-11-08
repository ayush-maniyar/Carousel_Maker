create table if not exists public.transcripts (
    video_id text not null,
    language text not null default 'und',
    transcript_text text not null,
    source text not null default 'native',
    created_at timestamptz not null default now(),
    primary key (video_id, language)
);

create table if not exists public.transcript_consents (
    token_hash text primary key,
    video_id text not null,
    expires_at timestamptz not null,
    consumed_at timestamptz,
    created_at timestamptz not null default now()
);

create index if not exists transcript_consents_expiry_idx
    on public.transcript_consents (expires_at);

create table if not exists public.transcript_generation_locks (
    video_id text primary key,
    owner_token text not null,
    expires_at timestamptz not null,
    created_at timestamptz not null default now()
);

alter table public.transcripts enable row level security;
alter table public.transcript_consents enable row level security;
alter table public.transcript_generation_locks enable row level security;

-- Backend-only access. Never expose the service-role key in frontend code.
revoke all privileges on table public.transcripts from anon, authenticated;
revoke all privileges on table public.transcript_consents from anon, authenticated;
revoke all privileges on table public.transcript_generation_locks from anon, authenticated;

grant select, insert, update, delete on table public.transcripts to service_role;
grant select, insert, update, delete on table public.transcript_consents to service_role;
grant select, insert, update, delete on table public.transcript_generation_locks to service_role;

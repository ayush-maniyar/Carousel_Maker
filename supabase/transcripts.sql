create table if not exists public.transcripts (
    video_id text primary key,
    language text not null default 'und',
    transcript_text text not null,
    source text not null default 'native',
    created_at timestamptz not null default now()
);

alter table public.transcripts enable row level security;

-- Backend access uses the Supabase service-role key, stored only in Render.
-- Do not expose the service-role key in the frontend.

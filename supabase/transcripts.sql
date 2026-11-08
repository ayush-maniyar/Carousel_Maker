create table if not exists public.transcripts (
    video_id text not null,
    language text not null default 'und',
    transcript_text text not null,
    source text not null default 'native',
    created_at timestamptz not null default now(),
    primary key (video_id, language)
);

alter table public.transcripts enable row level security;

-- Backend access uses the Supabase service-role key, stored only in Render.
-- Never expose the service-role key in frontend code.

-- Enable the pgvector extension if not already enabled
create extension if not exists vector;

-- Create the match_documents function
create or replace function match_documents (
  query_embedding vector(1536),
  match_threshold float,
  match_count int default 10
) returns table (
  id uuid,
  content text,
  title text,
  url text,
  similarity float
)
language sql stable
as $$
  select
    documents.id,
    documents.content,
    documents.title,
    documents.url,
    1 - (documents.embedding <=> query_embedding) as similarity
  from documents
  where 1 - (documents.embedding <=> query_embedding) > match_threshold
  order by similarity desc
  limit match_count;
$$;

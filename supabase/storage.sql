INSERT INTO storage.buckets (id, name, public, file_size_limit)
VALUES
    ('avatars', 'avatars', false, 5242880),
    ('chat-images', 'chat-images', false, 10485760),
    ('chat-files', 'chat-files', false, 52428800),
    ('statuses', 'statuses', false, 20971520)
ON CONFLICT (id) DO NOTHING;

CREATE POLICY "Authenticated users view avatars" ON storage.objects FOR SELECT TO authenticated USING (bucket_id = 'avatars');
CREATE POLICY "Users upload own avatar" ON storage.objects FOR INSERT TO authenticated WITH CHECK (bucket_id = 'avatars' AND (storage.foldername(name))[1] = auth.uid()::text);
CREATE POLICY "Users update own avatar" ON storage.objects FOR UPDATE TO authenticated USING (bucket_id = 'avatars' AND (storage.foldername(name))[1] = auth.uid()::text);
CREATE POLICY "Users delete own avatar" ON storage.objects FOR DELETE TO authenticated USING (bucket_id = 'avatars' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Conversation members access chat media" ON storage.objects FOR SELECT TO authenticated USING (bucket_id IN ('chat-images', 'chat-files') AND public.is_conversation_member(((storage.foldername(name))[1])::uuid, auth.uid()));
CREATE POLICY "Conversation members upload chat media" ON storage.objects FOR INSERT TO authenticated WITH CHECK (bucket_id IN ('chat-images', 'chat-files') AND public.is_conversation_member(((storage.foldername(name))[1])::uuid, auth.uid()) AND (storage.foldername(name))[2] = auth.uid()::text);

CREATE POLICY "Authorized contacts read status media" ON storage.objects FOR SELECT TO authenticated USING (bucket_id = 'statuses');
CREATE POLICY "Users upload own status media" ON storage.objects FOR INSERT TO authenticated WITH CHECK (bucket_id = 'statuses' AND (storage.foldername(name))[1] = auth.uid()::text);

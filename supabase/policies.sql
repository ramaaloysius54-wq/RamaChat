ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversation_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.message_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.statuses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.status_views ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.blocked_users ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION public.is_conversation_member(conv_id UUID, uid UUID)
RETURNS BOOLEAN LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.conversation_members
        WHERE conversation_id = conv_id AND user_id = uid
    );
$$;

CREATE OR REPLACE FUNCTION public.is_conversation_admin(conv_id UUID, uid UUID)
RETURNS BOOLEAN LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.conversation_members
        WHERE conversation_id = conv_id AND user_id = uid AND role = 'admin'
    );
$$;

CREATE OR REPLACE FUNCTION public.is_blocked(user_a UUID, user_b UUID)
RETURNS BOOLEAN LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.blocked_users
        WHERE (blocker_id = user_a AND blocked_id = user_b)
           OR (blocker_id = user_b AND blocked_id = user_a)
    );
$$;

CREATE POLICY "Read non-blocked profiles" ON public.profiles FOR SELECT TO authenticated USING (NOT public.is_blocked(auth.uid(), id));
CREATE POLICY "Insert own profile" ON public.profiles FOR INSERT TO authenticated WITH CHECK (auth.uid() = id);
CREATE POLICY "Update own profile" ON public.profiles FOR UPDATE TO authenticated USING (auth.uid() = id) WITH CHECK (auth.uid() = id);

CREATE POLICY "Select conversations for members" ON public.conversations FOR SELECT TO authenticated USING (public.is_conversation_member(id, auth.uid()) OR created_by = auth.uid());
CREATE POLICY "Create conversations" ON public.conversations FOR INSERT TO authenticated WITH CHECK (created_by = auth.uid());
CREATE POLICY "Update group conversations by admin" ON public.conversations FOR UPDATE TO authenticated USING (public.is_conversation_admin(id, auth.uid()));
CREATE POLICY "Delete group conversations by admin" ON public.conversations FOR DELETE TO authenticated USING (public.is_conversation_admin(id, auth.uid()));

CREATE POLICY "Select members in shared conversations" ON public.conversation_members FOR SELECT TO authenticated USING (public.is_conversation_member(conversation_id, auth.uid()));
CREATE POLICY "Insert creator or admin adds member" ON public.conversation_members FOR INSERT TO authenticated WITH CHECK (user_id = auth.uid() OR public.is_conversation_admin(conversation_id, auth.uid()));
CREATE POLICY "Leave conversation or admin removes member" ON public.conversation_members FOR DELETE TO authenticated USING (user_id = auth.uid() OR public.is_conversation_admin(conversation_id, auth.uid()));

CREATE POLICY "Members can read messages" ON public.messages FOR SELECT TO authenticated USING (public.is_conversation_member(conversation_id, auth.uid()));
CREATE POLICY "Members can send own messages" ON public.messages FOR INSERT TO authenticated WITH CHECK (sender_id = auth.uid() AND public.is_conversation_member(conversation_id, auth.uid()));
CREATE POLICY "Senders can edit own messages" ON public.messages FOR UPDATE TO authenticated USING (sender_id = auth.uid()) WITH CHECK (sender_id = auth.uid());
CREATE POLICY "Senders can delete own messages" ON public.messages FOR DELETE TO authenticated USING (sender_id = auth.uid());

CREATE POLICY "Members can read receipts" ON public.message_receipts FOR SELECT TO authenticated USING (EXISTS (SELECT 1 FROM public.messages m WHERE m.id = message_id AND public.is_conversation_member(m.conversation_id, auth.uid())));
CREATE POLICY "Users manage own receipts" ON public.message_receipts FOR ALL TO authenticated USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users manage own contacts" ON public.contacts FOR ALL TO authenticated USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

CREATE POLICY "View active statuses" ON public.statuses FOR SELECT TO authenticated USING (expires_at > NOW() AND NOT public.is_blocked(auth.uid(), user_id));
CREATE POLICY "Manage own statuses" ON public.statuses FOR ALL TO authenticated USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

CREATE POLICY "Read status views" ON public.status_views FOR SELECT TO authenticated USING (viewer_id = auth.uid() OR EXISTS (SELECT 1 FROM public.statuses s WHERE s.id = status_id AND s.user_id = auth.uid()));
CREATE POLICY "Insert own status view" ON public.status_views FOR INSERT TO authenticated WITH CHECK (viewer_id = auth.uid());

CREATE POLICY "Manage own block list" ON public.blocked_users FOR ALL TO authenticated USING (blocker_id = auth.uid()) WITH CHECK (blocker_id = auth.uid());

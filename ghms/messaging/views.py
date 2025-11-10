# messaging/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Max
from .models import Thread, Message
from core.models import StaffProfile
from audit.utils import log as hashchain_log
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from .utils import get_shift_status
from django.contrib import messages
from django.utils import timezone



User = get_user_model()

@login_required
def inbox(request):
    """
    Show conversation threads the current user is part of,
    ordered by last message.
    """
    threads = (
        Thread.objects.filter(participants=request.user)
        .annotate(last_message_at=Max("messages__created_at"))
        .order_by("-last_message_at")
    )

    return render(request, "messaging/inbox.html", {
        "threads": threads,
    })

@login_required
def thread_detail(request, thread_id):
    thread = get_object_or_404(
        Thread.objects.filter(participants=request.user),
        id=thread_id,
    )

    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        if body:
            msg = Message.objects.create(thread=thread, sender=request.user, body=body)
            hashchain_log("MSG_SENT", {
                "thread_id": thread.id,
                "sender_id": request.user.id,
            }, actor=request.user)
        return redirect("msg_thread", thread_id=thread.id)

    return render(request, "messaging/thread.html", {"thread": thread})


@login_required
def start_thread(request, user_id):
    target = get_object_or_404(User, id=user_id)

    sp = getattr(request.user, "staffprofile", None)
    tsp = getattr(target, "staffprofile", None)

    my_dept = getattr(sp, "department", None) if sp else None
    my_hospital = getattr(my_dept, "hospital", None) if my_dept else None

    t_dept = getattr(tsp, "department", None) if tsp else None
    t_hospital = getattr(t_dept, "hospital", None) if t_dept else None

    if not sp or not tsp:
        messages.error(request, "Both users must be registered staff.")
        return redirect("msg_inbox")

    # Same policy as compose:
    if my_hospital and t_hospital:
        if my_hospital != t_hospital:
            messages.error(request, "You can only message staff within your hospital.")
            return redirect("msg_inbox")
    else:
        if not my_dept or not t_dept or my_dept != t_dept:
            messages.error(request, "You can only message staff in your facility.")
            return redirect("msg_inbox")

    thread = (
        Thread.objects
        .filter(participants=request.user)
        .filter(participants=target)
        .first()
    )
    if not thread:
        thread = Thread.objects.create()
        thread.participants.add(request.user, target)

    return redirect("msg_thread", thread_id=thread.id)

@login_required
def message_compose(request):
    sp = getattr(request.user, "staffprofile", None)
    if not sp:
        messages.error(request, "Messaging is only available for registered staff.")
        return redirect("msg_inbox")

    my_hospital = getattr(sp, "hospital", None)
    my_dept = getattr(sp, "department", None)

    # ---------- SEND MESSAGE ----------
    if request.method == "POST":
        recipient_id = request.POST.get("recipient")
        body = request.POST.get("body", "").strip()

        if not recipient_id or not body:
            messages.error(request, "Select a recipient and enter a message.")
        else:
            recipient = get_object_or_404(User, id=recipient_id)
            rsp = getattr(recipient, "staffprofile", None)

            # Must have staffprofile
            if not rsp:
                messages.error(request, "Selected user is not a staff member.")
                return redirect("msg_compose")

            r_hospital = getattr(rsp, "hospital", None)
            r_dept = getattr(rsp, "department", None)

            # Policy:
            # 1) If both hospitals known -> must match.
            # 2) If hospital missing -> fall back to same department.
            if my_hospital and r_hospital:
                if my_hospital != r_hospital:
                    messages.error(request, "You can only message staff within your hospital.")
                    return redirect("msg_compose")
            else:
                if not my_dept or not r_dept or my_dept != r_dept:
                    messages.error(request, "You can only message staff in your facility.")
                    return redirect("msg_compose")

            # Find or create direct thread
            thread = (
                Thread.objects
                .filter(participants=request.user)
                .filter(participants=recipient)
                .first()
            )
            if not thread:
                thread = Thread.objects.create()
                thread.participants.add(request.user, recipient)

            Message.objects.create(
                thread=thread,
                sender=request.user,
                body=body,
            )

            hashchain_log("MSG_SENT", {
                "thread_id": thread.id,
                "sender_id": request.user.id,
                "recipient_id": recipient.id,
                "ts": timezone.now().isoformat(),
            }, actor=request.user)

            return redirect("msg_thread", thread_id=thread.id)

    # ---------- SEARCH RECIPIENTS ----------
    query = request.GET.get("q", "").strip()
    annotated = []

    if query:
        # Base queryset: active users, not self
        recipients_qs = (
            User.objects
            .filter(is_active=True)
            .exclude(id=request.user.id)
            .filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )
            .select_related(
                "staffprofile",
                "staffprofile__department",
                "staffprofile__hospital",
            )
            .order_by("first_name", "last_name")
        )

        # Restrict to same hospital if known
        if my_hospital:
            recipients_qs = recipients_qs.filter(staffprofile__hospital=my_hospital)
        # Fallback: same department only
        elif my_dept:
            recipients_qs = recipients_qs.filter(staffprofile__department=my_dept)

        for u in recipients_qs:
            # Only list people who actually have a staffprofile
            if not hasattr(u, "staffprofile"):
                continue
            annotated.append({
                "user": u,
                "shift_status": get_shift_status(u),
            })

    return render(request, "messaging/compose.html", {
        "recipients": annotated,
        "query": query,
    })
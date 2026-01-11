from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Q, Avg
from django.core.paginator import Paginator
import json

from .models import Category, Offer, Message, Trade, UserProfile, Review, Notification


# ==================== HOME ====================

def home(request):
    """Početna stranica"""
    active_offers = Offer.objects.filter(is_active=True).order_by('-created_at')[:6]
    categories = Category.objects.all()

    unread_count = 0

    if request.user.is_authenticated:
        unread_count = Message.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

    context = {
        'active_offers': active_offers,
        'categories': categories,
        'unread_count': unread_count,
        'show_messages': True,
    }
    return render(request, 'core/home.html', context)


# ==================== OFFERS ====================

def offer_list(request):
    """Lista svih ponuda sa pretragom i filteriranjem"""
    offers = Offer.objects.filter(is_active=True).order_by('-created_at')
    categories = Category.objects.all()

    query = request.GET.get('q', '')
    if query:
        offers = offers.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )

    category_id = request.GET.get('category', '')
    if category_id:
        offers = offers.filter(category_id=category_id)

    # ✅ NOVI KOD - FILTER PO KORISNIKU
    user = request.GET.get('user', '')
    if user:
        offers = offers.filter(owner__username=user)

    paginator = Paginator(offers, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'offers': page_obj.object_list,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
        'show_messages': False,
    }
    return render(request, 'core/offer_list.html', context)


def offer_detail(request, pk):
    """Detalj ponude"""
    offer = get_object_or_404(Offer, pk=pk)

    if request.user != offer.owner:
        offer.views_count += 1
        offer.save()

    reviews = offer.reviews.all().order_by('-created_at')

    context = {
        'offer': offer,
        'reviews': reviews,
        'show_messages': True,
    }
    return render(request, 'core/offer_detail.html', context)


@login_required(login_url='core:login')
def offer_create(request):
    """Kreiraj novu ponudu"""
    categories = Category.objects.all()

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category', '')
        image = request.FILES.get('image')
        price_range = request.POST.get('price_range', '')
        location = request.POST.get('location', '').strip()
        city = request.POST.get('city', '').strip()

        if not all([title, description, category_id, city]):
            messages.error(request, 'Molim popuni sve obavezne polje!')
            return redirect('core:offer_create')

        try:
            category = Category.objects.get(id=category_id)
            offer = Offer.objects.create(
                title=title,
                description=description,
                offered='Vidi u opisu',
                wanted='Vidi u opisu',
                category=category,
                owner=request.user,
                image=image,
                price_range=price_range,
                location=location,
                city=city,
            )
            messages.success(request, 'Ponuda je uspešno objavljena!')
            return redirect('core:offer_detail', pk=offer.pk)
        except Exception as e:
            messages.error(request, f'Greška pri kreiranju ponude: {str(e)}')
            return redirect('core:offer_create')

    context = {
        'categories': categories,
        'title': 'Kreiraj novu ponudu',
        'show_messages': True,
    }
    return render(request, 'core/offer_form.html', context)


@login_required(login_url='core:login')
def offer_edit(request, pk):
    """Ažuriraj ponudu"""
    offer = get_object_or_404(Offer, pk=pk)

    if offer.owner != request.user:
        messages.error(request, 'Nemaš pristup ovoj ponudi!')
        return redirect('core:home')

    categories = Category.objects.all()

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category', '')
        price_range = request.POST.get('price_range', '')
        location = request.POST.get('location', '').strip()
        city = request.POST.get('city', '').strip()

        if not all([title, description, category_id, city]):
            messages.error(request, 'Molim popuni sve obavezne polje!')
            return redirect('core:offer_edit', pk=pk)

        offer.title = title
        offer.description = description
        offer.category_id = category_id
        offer.price_range = price_range
        offer.location = location
        offer.city = city
        offer.offered = 'Vidi u opisu'
        offer.wanted = 'Vidi u opisu'

        if request.FILES.get('image'):
            offer.image = request.FILES.get('image')

        offer.save()
        messages.success(request, 'Ponuda je uspešno ažurirana!')
        return redirect('core:offer_detail', pk=offer.pk)

    context = {
        'offer': offer,
        'categories': categories,
        'title': 'Uredi ponudu',
        'show_messages': True,
    }
    return render(request, 'core/offer_form.html', context)


@login_required(login_url='core:login')
def offer_delete(request, pk):
    """Obriši ponudu"""
    offer = get_object_or_404(Offer, pk=pk)

    if offer.owner != request.user:
        messages.error(request, 'Nemaš pristup ovoj ponudi!')
        return redirect('core:home')

    if request.method == 'POST':
        offer_title = offer.title
        offer.delete()
        messages.success(request, f'Ponuda "{offer_title}" je obrisana!')
        return redirect('core:offer_list')

    context = {
        'offer': offer,
        'show_messages': True,
    }
    return render(request, 'core/offer_confirm_delete.html', context)


@login_required(login_url='core:login')
def my_offers(request):
    """Moje ponude"""
    offers = Offer.objects.filter(owner=request.user).order_by('-created_at')

    paginator = Paginator(offers, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'offers': page_obj.object_list,
        'show_messages': True,
    }
    return render(request, 'core/my_offers.html', context)


# ==================== PROFILE ====================

@login_required(login_url='core:login')
def profile_view(request):
    """Moj profil"""
    user_offers = request.user.offers.all().order_by('-created_at')

    # ✅ DOBIJ RECENZIJE KOJE JE OVAJ KORISNIK PRIMIO
    reviews = Review.objects.filter(reviewed_user=request.user).order_by('-created_at')

    # Izračunaj statistike
    active_offers = user_offers.filter(is_active=True).count()
    total_views = sum(offer.views_count for offer in user_offers)
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] if reviews else 0

    context = {
        'user_offers': user_offers,
        'active_offers': active_offers,
        'total_views': total_views,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1) if avg_rating else 0,
        'review_count': reviews.count(),
        'show_messages': True,
    }
    return render(request, 'core/profile.html', context)


def user_profile_view(request, username):
    """Pregled profila drugog korisnika"""
    profile_user = get_object_or_404(User, username=username)
    user_offers = profile_user.offers.filter(is_active=True).order_by('-created_at')[:6]
    reviews = Review.objects.filter(reviewed_user=profile_user).order_by('-created_at')

    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] if reviews else 0
    review_count = reviews.count()

    context = {
        'profile_user': profile_user,
        'user_offers': user_offers,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1) if avg_rating else 0,
        'review_count': review_count,
        'show_messages': True,
    }
    return render(request, 'core/user_profile.html', context)


# ==================== MESSAGES ====================

@login_required(login_url='core:login')
def my_messages(request):
    """Lista razgovora"""
    conversations = []

    sent_to = Message.objects.filter(sender=request.user).values_list('recipient', flat=True).distinct()
    received_from = Message.objects.filter(recipient=request.user).values_list('sender', flat=True).distinct()

    user_ids = set(sent_to) | set(received_from)

    unread_count = 0

    for user_id in user_ids:
        user = User.objects.get(id=user_id)
        last_message = Message.objects.filter(
            Q(sender=request.user, recipient=user) |
            Q(sender=user, recipient=request.user)
        ).order_by('-timestamp').first()

        user_unread = Message.objects.filter(
            sender=user,
            recipient=request.user,
            is_read=False
        ).count()

        unread_count += user_unread

        conversations.append({
            'user': user,
            'last_message': last_message,
            'unread_count': user_unread,
        })

    conversations.sort(
        key=lambda x: x['last_message'].timestamp if x['last_message'] else None,
        reverse=True
    )

    context = {
        'conversations': conversations,
        'unread_count': unread_count,
        'show_messages': True,
    }
    return render(request, 'core/my_messages.html', context)


@login_required(login_url='core:login')
def send_message(request, username):
    """Pošalji poruku - koristi username umesto ID-a"""
    recipient = get_object_or_404(User, username=username)

    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()

        if not body:
            messages.error(request, 'Poruka ne može biti prazna!')
            return redirect('core:send_message', username=username)

        message = Message.objects.create(
            sender=request.user,
            recipient=recipient,
            subject=subject,
            body=body,
        )

        messages.success(request, 'Poruka je poslata!')
        return redirect('core:my_messages')

    context = {
        'recipient': recipient,
        'show_messages': True,
    }
    return render(request, 'core/send_message.html', context)


@login_required(login_url='core:login')
def view_conversation(request, username):
    """Pregled razgovora sa korisnikom"""
    other_user = get_object_or_404(User, username=username)

    # HANDLE POST - Kreiraj novu poruku
    if request.method == 'POST':
        body = request.POST.get('body', '').strip()

        if body:
            Message.objects.create(
                sender=request.user,
                recipient=other_user,
                subject='',
                body=body,
            )
            messages.success(request, 'Poruka je poslata!')
        else:
            messages.error(request, 'Poruka ne može biti prazna!')

        return redirect('core:view_conversation', username=username)

    # GET - Prikaži sve poruke
    messages_list = Message.objects.filter(
        Q(sender=request.user, recipient=other_user) |
        Q(sender=other_user, recipient=request.user)
    ).order_by('timestamp')

    # Označi sve primljene poruke kao pročitane
    Message.objects.filter(
        sender=other_user,
        recipient=request.user,
        is_read=False
    ).update(is_read=True)

    context = {
        'other_user': other_user,
        'messages': messages_list,
        'show_messages': True,
    }
    return render(request, 'core/conversation.html', context)


# ==================== TRADES ====================

@login_required(login_url='core:login')
def my_trades(request):
    """Moje razmene"""
    sent_trades = Trade.objects.filter(user1=request.user).order_by('-created_at')
    received_trades = Trade.objects.filter(user2=request.user).order_by('-created_at')

    context = {
        'sent_trades': sent_trades,
        'received_trades': received_trades,
        'show_messages': True,
    }
    return render(request, 'core/trades.html', context)


@login_required(login_url='core:login')
def create_trade(request, offer_id):
    """Kreiraj zahtev za razmenu"""
    offer2 = get_object_or_404(Offer, pk=offer_id)

    if offer2.owner == request.user:
        messages.error(request, 'Ne možeš razmeniti sopstvenu ponudu!')
        return redirect('core:offer_detail', pk=offer_id)

    if request.method == 'POST':
        # ✅ ČITAJ DODATNU PORUKU I CHECKBOX
        additional_message = request.POST.get('additional_message', '').strip()
        wants_to_buy = request.POST.get('wants_to_buy')

        # ✅ AUTOMATSKA PORUKA
        base_message = 'Postovani, zainteresovan/a sam za vasu ponudu. Molim Vas pogledajte moje oglase za mogucu razmenu.'

        # ✅ KOMBINUJ AUTOMATSKU + DODATNU PORUKU
        if additional_message:
            full_message = f"{base_message}\n\n{additional_message}"
        else:
            full_message = base_message

        # ✅ KREIRAJ TRADE BEZ IZBORA PONUDE
        trade = Trade.objects.create(
            offer1=None,
            offer2=offer2,
            user1=request.user,
            user2=offer2.owner,
            message=full_message,
        )

        # ✅ NOVA NOTIFIKACIJA
        notification_message = f'{request.user.username} je zainteresovan/a za vasu ponudu. Pogledajte oglase za potencijalnu razmenu, ili otkup.'

        Notification.objects.create(
            recipient=offer2.owner,
            title=f'Nova ponuda od {request.user.username}',
            message=notification_message,
            notification_type='trade',
        )

        messages.success(request, 'Zahtev za razmenu je poslat!')
        return redirect('core:my_trades')

    context = {
        'offer2': offer2,
        'show_messages': True,
    }
    return render(request, 'core/create_trade.html', context)


@login_required(login_url='core:login')
def trade_detail(request, pk):
    """Detalj razmene"""
    trade = get_object_or_404(Trade, pk=pk)

    if request.user not in [trade.user1, trade.user2]:
        messages.error(request, 'Nemaš dozvolu za ovu akciju!')
        return redirect('core:home')

    # ✅ NOVO - Sve ponude od user1
    user1_offers = Offer.objects.filter(owner=trade.user1, is_active=True)

    context = {
        'trade': trade,
        'user1_offers': user1_offers,
        'show_messages': True,
    }
    return render(request, 'core/trade_detail.html', context)


@login_required(login_url='core:login')
def accept_trade_with_offer(request, pk, offer_id):
    """Prihvati razmenu sa odabranim artiklom"""
    trade = get_object_or_404(Trade, pk=pk)
    selected_offer = get_object_or_404(Offer, pk=offer_id)

    if trade.user2 != request.user:
        messages.error(request, 'Nemaš dozvolu za ovu akciju!')
        return redirect('core:my_trades')

    # Provjeri da odabrani artikal pripada user1
    if selected_offer.owner != trade.user1:
        messages.error(request, 'Nedozvoljen izbor!')
        return redirect('core:trade_detail', pk=pk)

    if request.method == 'POST':
        # ✅ POSTAVI odabranu ponudu kao offer1
        trade.offer1 = selected_offer
        trade.status = 'accepted'
        trade.save()

        # Kreiraj notifikaciju
        Notification.objects.create(
            recipient=trade.user1,
            actor=trade.user2,
            title='Razmena prihvaćena!',
            message=f'{trade.user2.username} je prihvatio vašu razmenu sa artiklom "{selected_offer.title}"!',
            notification_type='trade_accepted',
            trade=trade,
        )

        messages.success(request, 'Razmena je prihvaćena!')
        return redirect('core:my_trades')

    context = {
        'trade': trade,
        'selected_offer': selected_offer,
        'show_messages': True,
    }
    return render(request, 'core/confirm_action.html', context)


@login_required(login_url='core:login')
def accept_trade_buy(request, pk):
    """Prihvati razmenu sa opcijom za otkup"""
    trade = get_object_or_404(Trade, pk=pk)

    if trade.user2 != request.user:
        messages.error(request, 'Nemaš dozvolu za ovu akciju!')
        return redirect('core:my_trades')

    if not trade.wants_to_buy:
        messages.error(request, 'Opcija za otkup nije dostupna!')
        return redirect('core:trade_detail', pk=pk)

    if request.method == 'POST':
        # ✅ POSTAVI offer1 na None (otkup bez zamjene)
        trade.offer1 = None
        trade.status = 'accepted'
        trade.save()

        # Kreiraj notifikaciju
        Notification.objects.create(
            recipient=trade.user1,
            actor=trade.user2,
            title='Otkup prihvaćen!',
            message=f'{trade.user2.username} je prihvatio vašu ponudu za otkup od {trade.purchase_price} дин.!',
            notification_type='trade_accepted',
            trade=trade,
        )

        messages.success(request, 'Otkup je prihvaćen!')
        return redirect('core:my_trades')

    context = {
        'trade': trade,
        'action': f'Kupi za {trade.purchase_price} дин.',
        'show_messages': True,
    }
    return render(request, 'core/confirm_action.html', context)


@login_required(login_url='core:login')
def accept_trade(request, pk):
    """Prihvati razmenu"""
    trade = get_object_or_404(Trade, pk=pk)

    if trade.user2 != request.user:
        messages.error(request, 'Nemaš dozvolu za ovu akciju!')
        return redirect('core:my_trades')

    if request.method == 'POST':
        trade.status = 'accepted'
        trade.save()

        # ✅ KREIRAJ NOTIFIKACIJU ZA RAZMENU
        Notification.objects.create(
            recipient=trade.user1,
            title='Razmena prihvaćena!',
            message=f'{trade.user2.username} je prihvatio vašu razmenu!',
            notification_type='trade',
        )

        messages.success(request, 'Razmena je prihvaćena!')
        return redirect('core:my_trades')

    context = {
        'trade': trade,
        'show_messages': True,
    }
    return render(request, 'core/confirm_action.html', context)


@login_required(login_url='core:login')
def reject_trade(request, pk):
    """Odbij razmenu"""
    trade = get_object_or_404(Trade, pk=pk)

    if trade.user2 != request.user:
        messages.error(request, 'Nemaš dozvolu za ovu akciju!')
        return redirect('core:my_trades')

    if request.method == 'POST':
        trade.status = 'rejected'
        trade.save()

        # ✅ KREIRAJ NOTIFIKACIJU ZA RAZMENU
        Notification.objects.create(
            recipient=trade.user1,
            title='Razmena odbijena',
            message=f'{trade.user2.username} je odbio vašu razmenu.',
            notification_type='trade',
        )

        messages.success(request, 'Razmena je odbijena!')
        return redirect('core:my_trades')

    context = {
        'trade': trade,
        'show_messages': True,
    }
    return render(request, 'core/confirm_action.html', context)


@login_required(login_url='core:login')
def complete_trade(request, pk):
    """Završi razmenu"""
    trade = get_object_or_404(Trade, pk=pk)

    if request.user not in [trade.user1, trade.user2]:
        messages.error(request, 'Nemaš dozvolu za ovu akciju!')
        return redirect('core:my_trades')

    if request.method == 'POST':
        trade.status = 'completed'
        trade.save()

        if trade.offer1:
            trade.offer1.is_active = False
            trade.offer1.save()

        trade.offer2.is_active = False
        trade.offer2.save()

        other_user = trade.user1 if request.user == trade.user2 else trade.user2

        # ✅ KREIRAJ NOTIFIKACIJU ZA RAZMENU
        Notification.objects.create(
            recipient=other_user,
            title='Razmena završena!',
            message=f'{request.user.username} je završio razmenu.',
            notification_type='trade',
        )

        messages.success(request, 'Razmena je završena! Sada možeš da napišeš recenziju.')
        return redirect('core:my_trades')

    context = {
        'trade': trade,
        'show_messages': True,
    }
    return render(request, 'core/confirm_action.html', context)


# ==================== REVIEWS ====================

@login_required(login_url='core:login')
def add_review(request, username):
    """Dodaj recenziju za korisnika"""
    reviewed_user = get_object_or_404(User, username=username)

    if reviewed_user == request.user:
        messages.error(request, 'Nemaš dozvolu da napišeš recenziju za sebe!')
        return redirect('core:user_profile_view', username=username)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()
        trade_id = request.POST.get('trade_id')

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, 'Ocena mora biti između 1 i 5!')
            return redirect('core:user_profile_view', username=username)

        try:
            trade = get_object_or_404(Trade, pk=trade_id) if trade_id else None

            if trade and Review.objects.filter(
                    reviewer=request.user,
                    reviewed_user=reviewed_user,
                    trade=trade
            ).exists():
                messages.warning(request, 'Već si napisao recenziju za ovu razmenu!')
                return redirect('core:user_profile_view', username=username)

            review = Review.objects.create(
                reviewer=request.user,
                reviewed_user=reviewed_user,
                rating=rating,
                comment=comment,
                trade=trade,
                is_verified_purchase=trade is not None,
            )

            messages.success(request, 'Recenzija je uspešno objavljena!')
            return redirect('core:user_profile_view', username=username)

        except Exception as e:
            messages.error(request, f'Greška: {str(e)}')
            return redirect('core:user_profile_view', username=username)

    context = {
        'reviewed_user': reviewed_user,
        'show_messages': True,
    }
    return render(request, 'core/add_review.html', context)


# ==================== NOTIFICATIONS ====================

@login_required(login_url='core:login')
def notifications_view(request):
    """Prikazi sve notifikacije korisnika"""
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    if request.GET.get('mark_all_read'):
        notifications.filter(is_read=False).update(is_read=True)
        messages.success(request, 'Sve notifikacije su označene kao pročitane!')
        return redirect('core:notifications')

    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'notifications': page_obj.object_list,
        'show_messages': True,
    }
    return render(request, 'core/notifications.html', context)


@login_required(login_url='core:login')
def mark_notification_read(request, pk):
    """Označi notifikaciju kao pročitanu"""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save()

    messages.success(request, 'Notifikacija je pročitana!')
    return redirect('core:notifications')


@login_required(login_url='core:login')
def delete_notification(request, pk):
    """Obriši notifikaciju"""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.delete()
    messages.success(request, 'Notifikacija je obrisana!')
    return redirect('core:notifications')


# ==================== AUTHENTICATION ====================

def login_view(request):
    """Login"""
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Dobrodošli, {user.username}!')
            return redirect('core:home')
        else:
            messages.error(request, 'Pogrešno korisničko ime ili lozinka!')

    return render(request, 'core/login.html')


@login_required(login_url='core:login')
def logout_view(request):
    """Logout"""
    logout(request)
    messages.success(request, 'Odjavili ste se!')
    return redirect('core:home')


def register_view(request):
    """Registracija"""
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        if password != password2:
            messages.error(request, 'Lozinke se ne poklapaju!')
            return redirect('core:register')

        if len(password) < 6:
            messages.error(request, 'Lozinka mora imati najmanje 6 karaktera!')
            return redirect('core:register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Korisničko ime je već zauzeto!')
            return redirect('core:register')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email je već registrovan!')
            return redirect('core:register')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        UserProfile.objects.create(user=user)

        messages.success(request, 'Nalog je kreiran! Sada se možeš ulogovati.')
        return redirect('core:login')

    return render(request, 'core/register.html')


# ==================== API ENDPOINTS ====================

@login_required(login_url='core:login')
@require_http_methods(["GET"])
def get_unread_count(request):
    """API endpoint - broj nepročitanih poruka i notifikacija"""
    unread_messages = Message.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    unread_notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    return JsonResponse({
        'unread_count': unread_notifications,
        'unread_messages': unread_messages,
        'success': True,
    })


@require_http_methods(["GET"])
def get_offer_stats(request, pk):
    """API endpoint - statistika ponude"""
    offer = get_object_or_404(Offer, pk=pk)

    stats = {
        'id': offer.id,
        'title': offer.title,
        'views': offer.views_count,
        'trades': Trade.objects.filter(
            Q(offer1=offer) | Q(offer2=offer)
        ).count(),
        'success': True,
    }

    return JsonResponse(stats)


@require_http_methods(["GET"])
def get_user_stats(request, username):
    """API endpoint - statistika korisnika"""
    user = get_object_or_404(User, username=username)

    reviews = Review.objects.filter(reviewed_user=user)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    stats = {
        'username': user.username,
        'total_offers': Offer.objects.filter(owner=user).count(),
        'active_offers': Offer.objects.filter(owner=user, is_active=True).count(),
        'completed_trades': Trade.objects.filter(
            Q(user1=user) | Q(user2=user),
            status='completed'
        ).count(),
        'reviews_count': reviews.count(),
        'average_rating': round(avg_rating, 1),
        'joined_date': user.date_joined.strftime('%Y-%m-%d'),
        'success': True,
    }

    return JsonResponse(stats)


@require_http_methods(["GET"])
def get_categories(request):
    """API endpoint - sve kategorije"""
    categories = Category.objects.all().values('id', 'name', 'description')

    categories_list = list(categories)

    return JsonResponse({
        'categories': categories_list,
        'count': len(categories_list),
        'success': True,
    })


@require_http_methods(["GET"])
def search_offers(request):
    """API endpoint - pretraga ponuda"""
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    city = request.GET.get('city', '').strip()
    page = request.GET.get('page', 1)

    offers = Offer.objects.filter(is_active=True)

    if query:
        offers = offers.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(offered__icontains=query) |
            Q(wanted__icontains=query)
        )

    if category_id:
        offers = offers.filter(category_id=category_id)

    if city:
        offers = offers.filter(city__icontains=city)

    paginator = Paginator(offers.order_by('-created_at'), 12)
    page_obj = paginator.get_page(page)

    offers_data = [
        {
            'id': offer.id,
            'title': offer.title,
            'offered': offer.offered,
            'wanted': offer.wanted,
            'city': offer.city,
            'owner': offer.owner.username,
            'created_at': offer.created_at.strftime('%Y-%m-%d %H:%M'),
        }
        for offer in page_obj.object_list
    ]

    return JsonResponse({
        'offers': offers_data,
        'total_count': offers.count(),
        'page': page_obj.number,
        'total_pages': paginator.num_pages,
        'success': True,
    })


@login_required(login_url='core:login')
@require_http_methods(["GET"])
def get_messages_list(request):
    """API endpoint - lista poruka kao JSON"""
    username = request.GET.get('username')
    page = request.GET.get('page', 1)

    if not username:
        return JsonResponse({
            'success': False,
            'error': 'Nedostaje username'
        }, status=400)

    other_user = get_object_or_404(User, username=username)

    messages_list = Message.objects.filter(
        Q(sender=request.user, recipient=other_user) |
        Q(sender=other_user, recipient=request.user)
    ).order_by('-timestamp')

    Message.objects.filter(
        sender=other_user,
        recipient=request.user,
        is_read=False
    ).update(is_read=True)

    paginator = Paginator(messages_list, 20)
    page_obj = paginator.get_page(page)

    messages_data = [
        {
            'id': msg.id,
            'sender': msg.sender.username,
            'subject': msg.subject,
            'body': msg.body,
            'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'is_read': msg.is_read,
        }
        for msg in page_obj.object_list
    ]

    return JsonResponse({
        'messages': messages_data,
        'other_user': {
            'username': other_user.username,
            'id': other_user.id,
        },
        'page': page_obj.number,
        'total_pages': paginator.num_pages,
        'success': True,
    })


@login_required(login_url='core:login')
@require_http_methods(["GET"])
def get_trades_list(request):
    """API endpoint - lista razmena kao JSON"""
    status_filter = request.GET.get('status')
    direction = request.GET.get('direction')

    if direction == 'sent':
        trades = Trade.objects.filter(user1=request.user)
    elif direction == 'received':
        trades = Trade.objects.filter(user2=request.user)
    else:
        trades = Trade.objects.filter(
            Q(user1=request.user) | Q(user2=request.user)
        )

    if status_filter:
        trades = trades.filter(status=status_filter)

    trades = trades.order_by('-created_at')

    trades_data = [
        {
            'id': trade.id,
            'offer1': {
                'id': trade.offer1.id,
                'title': trade.offer1.title,
                'owner': trade.offer1.owner.username,
            } if trade.offer1 else None,
            'offer2': {
                'id': trade.offer2.id,
                'title': trade.offer2.title,
                'owner': trade.offer2.owner.username,
            },
            'status': trade.status,
            'created_at': trade.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'message': trade.message,
        }
        for trade in trades
    ]

    return JsonResponse({
        'trades': trades_data,
        'total_count': trades.count(),
        'success': True,
    })


@require_http_methods(["GET"])
def get_offer_detail_api(request, pk):
    """API endpoint - detalj ponude kao JSON"""
    offer = get_object_or_404(Offer, pk=pk)

    owner_reviews = Review.objects.filter(reviewed_user=offer.owner)
    avg_rating = owner_reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    offer_data = {
        'id': offer.id,
        'title': offer.title,
        'description': offer.description,
        'offered': offer.offered,
        'wanted': offer.wanted,
        'category': {
            'id': offer.category.id,
            'name': offer.category.name,
        },
        'owner': {
            'username': offer.owner.username,
            'id': offer.owner.id,
            'rating': round(avg_rating, 1),
            'reviews_count': owner_reviews.count(),
        },
        'image_url': offer.image.url if offer.image else None,
        'price_range': offer.price_range,
        'location': offer.location,
        'city': offer.city,
        'views': offer.views_count,
        'is_active': offer.is_active,
        'created_at': offer.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': offer.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
    }

    return JsonResponse({
        'offer': offer_data,
        'success': True,
    })


@require_http_methods(["GET"])
def get_user_detail_api(request, username):
    """API endpoint - detalj korisnika kao JSON"""
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(UserProfile, user=user)

    reviews = Review.objects.filter(reviewed_user=user)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email if request.user == user else None,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'joined_date': user.date_joined.strftime('%Y-%m-%d'),
        'profile': {
            'bio': profile.bio,
            'location': profile.location,
            'phone': profile.phone if request.user == user else None,
        },
        'stats': {
            'total_offers': Offer.objects.filter(owner=user).count(),
            'active_offers': Offer.objects.filter(owner=user, is_active=True).count(),
            'completed_trades': Trade.objects.filter(
                Q(user1=user) | Q(user2=user),
                status='completed'
            ).count(),
            'reviews_count': reviews.count(),
            'average_rating': round(avg_rating, 1),
        }
    }

    return JsonResponse({
        'user': user_data,
        'success': True,
    })

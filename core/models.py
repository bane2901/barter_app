from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kategorija"
        verbose_name_plural = "Kategorije"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.name.lower().replace(' ', '-')
        super().save(*args, **kwargs)

    @property
    def offer_count(self):
        return self.offers.filter(is_active=True).count()


class Offer(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    description = models.TextField()
    offered = models.TextField()  # Šta nudi
    wanted = models.TextField()  # Šta traži
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='offers',
        default=1
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offers')
    image = models.ImageField(upload_to='offers/%Y/%m/%d/', blank=True, null=True)
    price_range = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, default="Srbija")
    city = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'created_at']),
            models.Index(fields=['category', 'is_active']),
        ]

    def __str__(self):
        return f"{self.title} ({self.owner.username})"

    def get_absolute_url(self):
        return reverse('core:offer_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{self.title}-{self.id}".lower().replace(' ', '-')
        super().save(*args, **kwargs)

    @property
    def main_image(self):
        if self.image:
            return self.image.url
        return '/static/images/no-image.jpg'

    @property
    def has_multiple_images(self):
        return False


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.sender.username} → {self.recipient.username}: {self.body[:50]}"

    @property
    def short_body(self):
        return self.body[:100] + '...' if len(self.body) > 100 else self.body


class Trade(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Čeka odobrenje'),
        ('accepted', 'Prihvaćeno'),
        ('rejected', 'Odbijeno'),
        ('cancelled', 'Otkazano'),
        ('completed', 'Završeno'),
    ]

    # ✅ PROMENJENO - DODAJ null=True, blank=True
    offer1 = models.ForeignKey(
        Offer,
        on_delete=models.CASCADE,
        related_name='trades_as_offer1',
        null=True,
        blank=True
    )
    offer2 = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='trades_as_offer2')
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trades_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trades_as_user2')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, null=True)

    # ✅ NOVO - Opcija za otkup
    wants_to_buy = models.BooleanField(default=False)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        offer1_title = self.offer1.title if self.offer1 else "Bez ponude"
        return f"{offer1_title} ↔ {self.offer2.title} ({self.get_status_display()})"

    @property
    def other_user(self):
        return self.user2 if self.user1 else self.user1

    @property
    def status_badge(self):
        colors = {
            'pending': 'warning',
            'accepted': 'success',
            'rejected': 'danger',
            'cancelled': 'secondary',
            'completed': 'primary'
        }
        return colors.get(self.status, 'info')


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True, default="Srbija")
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    rating = models.FloatField(default=5.0)
    trades_completed = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Profil korisnika"
        verbose_name_plural = "Profili korisnika"

    def __str__(self):
        return f"Profil {self.user.username}"

    @property
    def average_rating(self):
        """Prosečna ocena korisnika"""
        reviews = Review.objects.filter(reviewed_user=self.user)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0.0

    @property
    def total_reviews(self):
        """Ukupan broj recenzija"""
        return Review.objects.filter(reviewed_user=self.user).count()


class Review(models.Model):
    RATING_CHOICES = [
        (1, '⭐ Loše'),
        (2, '⭐⭐ Okej'),
        (3, '⭐⭐⭐ Dobro'),
        (4, '⭐⭐⭐⭐ Vrlo dobro'),
        (5, '⭐⭐⭐⭐⭐ Odličnom'),
    ]

    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    reviewed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='reviews')
    trade = models.ForeignKey(Trade, on_delete=models.CASCADE, related_name='reviews', blank=True, null=True)

    rating = models.PositiveIntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(max_length=500, blank=True)

    is_verified_purchase = models.BooleanField(default=False)
    is_positive = models.BooleanField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['reviewer', 'reviewed_user', 'offer']
        indexes = [
            models.Index(fields=['reviewed_user', 'rating']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = "Recenzija"
        verbose_name_plural = "Recenzije"

    def __str__(self):
        return f"{self.reviewer.username} → {self.reviewed_user.username}: {self.get_rating_display()}"

    def get_rating_display(self):
        return dict(self.RATING_CHOICES).get(self.rating, '')

    @property
    def is_recent(self):
        """Da li je recenzija novija od 7 dana"""
        from datetime import timedelta
        from django.utils import timezone
        return self.created_at >= timezone.now() - timedelta(days=7)


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('message', '💬 Nova poruka'),
        ('trade_request', '🤝 Zahtev za razmenu'),
        ('trade_accepted', '✅ Razmena prihvaćena'),
        ('trade_rejected', '❌ Razmena odbljena'),
        ('review', '⭐ Nova recenzija'),
        ('offer_liked', '❤️ Ponuda vam se dopala'),
        ('offer_viewed', '👁️ Neko pogledao vašu ponudu'),
        ('trade', '🤝 Razmena'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_sent', blank=True, null=True)

    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()

    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, blank=True, null=True, related_name='notifications')
    trade = models.ForeignKey(Trade, on_delete=models.CASCADE, blank=True, null=True, related_name='notifications')

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = "Notifikacija"
        verbose_name_plural = "Notifikacije"

    def __str__(self):
        return f"{self.get_notification_type_display()} → {self.recipient.username}"

    @property
    def is_recent(self):
        """Da li je notifikacija novija od 24 sata"""
        from datetime import timedelta
        from django.utils import timezone
        return self.created_at >= timezone.now() - timedelta(hours=24)


# ============================================
# SIGNALI - Automatske akcije
# ============================================



@receiver(post_save, sender=User)
def save_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=Offer)
def update_offer_slug(sender, instance, created, **kwargs):
    """Automatski generiši slug kada se kreirа nova ponuda"""
    if created and not instance.slug:
        instance.slug = f"{instance.title}-{instance.id}".lower().replace(' ', '-')
        instance.save(update_fields=['slug'])


@receiver(post_save, sender=Review)
def update_user_rating(sender, instance, created, **kwargs):
    """Ažuriraj prosečnu ocenu korisnika kada se doda nova recenzija"""
    if created:
        # Ažuriraj rating u UserProfile-u
        user_profile = instance.reviewed_user.userprofile
        avg_rating = user_profile.average_rating
        if avg_rating > 0:
            user_profile.rating = avg_rating
            user_profile.save(update_fields=['rating'])

        # Kreiraj notifikaciju za recenziju
        Notification.objects.create(
            recipient=instance.reviewed_user,
            actor=instance.reviewer,
            notification_type='review',
            title=f"Nova recenzija od {instance.reviewer.username}",
            message=f"{instance.reviewer.username} vam je dao ocenu: {instance.get_rating_display()}",
            offer=instance.offer,
        )


@receiver(post_save, sender=Trade)
def create_trade_notification(sender, instance, created=False, **kwargs):
    """Kreiraj notifikaciju za zahtev za razmenu"""
    if created:
        Notification.objects.create(
            recipient=instance.user2,
            actor=instance.user1,
            notification_type='trade_request',
            title=f"Zahtev za razmenu od {instance.user1.username}",
            message=f"{instance.user1.username} je poslao zahtev za razmenu: {instance.offer2.title}",
            trade=instance,
        )
    elif instance.status == 'accepted':
        # Notifikacija za prihvatenu razmenu
        Notification.objects.create(
            recipient=instance.user1,
            actor=instance.user2,
            notification_type='trade_accepted',
            title=f"Razmena prihvaćena od {instance.user2.username}",
            message=f"{instance.user2.username} je prihvatio vašu razmenu!",
            trade=instance,
        )
    elif instance.status == 'rejected':
        # Notifikacija za odbijena razmena
        Notification.objects.create(
            recipient=instance.user1,
            actor=instance.user2,
            notification_type='trade_rejected',
            title=f"Razmena odbijena od {instance.user2.username}",
            message=f"{instance.user2.username} je odbio vašu razmenu.",
            trade=instance,
        )

icon = models.CharField(max_length=50, default='fa-circle', blank=True)

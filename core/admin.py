from django.contrib import admin
from .models import Category, Offer, Message, Trade, UserProfile, Review, Notification


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'offer_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'category', 'is_active', 'is_premium', 'created_at')
    list_filter = ('is_active', 'is_premium', 'category', 'created_at')
    search_fields = ('title', 'description', 'owner__username')
    readonly_fields = ('slug', 'views_count', 'likes_count', 'created_at', 'updated_at')
    fieldsets = (
        ('Osnovne informacije', {
            'fields': ('title', 'slug', 'description', 'category', 'owner')
        }),
        ('Detalji razmene', {
            'fields': ('offered', 'wanted', 'price_range')
        }),
        ('Lokacija', {
            'fields': ('location', 'city')
        }),
        ('Multimedija', {
            'fields': ('image',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_premium')
        }),
        ('Statistika', {
            'fields': ('views_count', 'likes_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ('-created_at',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'subject', 'is_read', 'timestamp')
    list_filter = ('is_read', 'timestamp')
    search_fields = ('sender__username', 'recipient__username', 'subject', 'body')
    readonly_fields = ('timestamp', 'sender', 'recipient')
    ordering = ('-timestamp',)


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ('offer1', 'offer2', 'user1', 'user2', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('offer1__title', 'offer2__title', 'user1__username', 'user2__username')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Ponude', {
            'fields': ('offer1', 'offer2')
        }),
        ('Korisnici', {
            'fields': ('user1', 'user2')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Poruka', {
            'fields': ('message',)
        }),
        ('Vremenske marke', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ('-created_at',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'rating', 'is_verified', 'trades_completed', 'total_reviews')
    list_filter = ('is_verified', 'rating')
    search_fields = ('user__username', 'user__email', 'location')
    readonly_fields = ('created_at', 'average_rating', 'total_reviews')
    fieldsets = (
        ('Korisnik', {
            'fields': ('user',)
        }),
        ('Osnovne informacije', {
            'fields': ('phone', 'location', 'bio', 'avatar')
        }),
        ('Reputacija', {
            'fields': ('rating', 'average_rating', 'total_reviews', 'trades_completed', 'is_verified')
        }),
        ('Vremenske marke', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    ordering = ('user__username',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'reviewed_user', 'rating', 'offer', 'is_verified_purchase', 'created_at')
    list_filter = ('rating', 'is_verified_purchase', 'created_at', 'is_positive')
    search_fields = ('reviewer__username', 'reviewed_user__username', 'offer__title', 'comment')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Recenzija', {
            'fields': ('reviewer', 'reviewed_user', 'offer', 'trade')
        }),
        ('Ocena', {
            'fields': ('rating', 'comment', 'is_positive')
        }),
        ('Verifikacija', {
            'fields': ('is_verified_purchase',)
        }),
        ('Vremenske marke', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ('-created_at',)

    def get_readonly_fields(self, request, obj=None):
        """Zabrani editovanje reviewer-a i reviewed_user-a nakon kreiranja"""
        if obj:  # Ako se edituje postojeći objekat
            return self.readonly_fields + ['reviewer', 'reviewed_user', 'offer']
        return self.readonly_fields


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'actor__username', 'title', 'message')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Primalac', {
            'fields': ('recipient', 'actor')
        }),
        ('Notifikacija', {
            'fields': ('notification_type', 'title', 'message')
        }),
        ('Reference', {
            'fields': ('offer', 'trade'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
        ('Vremenske marke', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ('-created_at',)

    def get_readonly_fields(self, request, obj=None):
        """Čini sve polje read-only nakon kreiranja"""
        if obj:
            return self.readonly_fields + ['recipient', 'actor', 'notification_type', 'title', 'message', 'offer',
                                           'trade', 'is_read']
        return self.readonly_fields

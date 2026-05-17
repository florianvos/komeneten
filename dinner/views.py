import calendar
from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import InvitationForm, MenuTeaserForm, ScoreForm
from .models import Availability, Couple, DinnerDate, Invitation, MenuTeaser, Score

COMPETITION_YEAR = 2026
COMPETITION_MONTHS = [7, 8]


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user:
            login(request, user)
            return redirect('home')
        messages.error(request, 'Ongeldig gebruikersnaam of wachtwoord.')
    return render(request, 'dinner/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def home(request):
    try:
        couple = request.user.couple
    except Exception:
        couple = None
    couples = Couple.objects.select_related('user').prefetch_related('invitation', 'hosted_dinners__teaser').all()
    return render(request, 'dinner/home.html', {'couple': couple, 'couples': couples})


@login_required
def edit_invitation_view(request):
    try:
        couple = request.user.couple
    except Exception:
        messages.error(request, 'Geen koppelprofiel gevonden.')
        return redirect('home')

    invitation = getattr(couple, 'invitation', None)

    if request.method == 'POST':
        form = InvitationForm(request.POST, instance=invitation)
        if form.is_valid():
            inv = form.save(commit=False)
            inv.couple = couple
            inv.save()
            messages.success(request, 'Uitnodiging opgeslagen!')
            return redirect('home')
    else:
        form = InvitationForm(instance=invitation)

    return render(request, 'dinner/edit_invitation.html', {'form': form, 'couple': couple})


def _build_month_grid(year, month, dinner_dates, availability_map, my_available_dates, total_couples, couple, today):
    cal = calendar.Calendar(firstweekday=0)
    weeks = cal.monthdatescalendar(year, month)
    result = []
    for week in weeks:
        week_data = []
        for day in week:
            if day.month == month:
                dinner = dinner_dates.get(day)
                available_names = availability_map.get(day, [])
                i_am_available = day in my_available_dates
                is_proposed = dinner is None and len(available_names) >= total_couples
                avail_count = len(available_names)
                week_data.append({
                    'date': day,
                    'dinner': dinner,
                    'is_my_dinner': dinner is not None and dinner.host == couple,
                    'is_past': day < today,
                    'in_month': True,
                    'available_names': available_names,
                    'avail_count': avail_count,
                    'empty_dots': range(max(0, total_couples - avail_count)),
                    'i_am_available': i_am_available,
                    'is_proposed': is_proposed,
                    'total_couples': total_couples,
                })
            else:
                week_data.append({'in_month': False, 'date': day})
        result.append(week_data)
    return result


@login_required
def calendar_view(request):
    try:
        couple = request.user.couple
    except Exception:
        couple = None
    today = date.today()
    total_couples = Couple.objects.count()

    if request.method == 'POST':
        if couple is None:
            messages.error(request, 'Supergebruiker heeft geen koppelprofiel om beschikbaarheid te markeren.')
            return redirect('calendar')

        date_str = request.POST.get('date')
        try:
            target_date = date.fromisoformat(date_str)
        except (ValueError, TypeError):
            messages.error(request, 'Ongeldige datum.')
            return redirect('calendar')

        if target_date < today:
            messages.error(request, 'Je kan geen datum in het verleden selecteren.')
            return redirect('calendar')

        if DinnerDate.objects.filter(date=target_date).exists():
            messages.error(request, 'Die datum is al bevestigd als diner.')
            return redirect('calendar')

        obj, created = Availability.objects.get_or_create(couple=couple, date=target_date)
        if not created:
            obj.delete()
            messages.success(request, f'Beschikbaarheid op {target_date.strftime("%d %B")} verwijderd.')
        else:
            messages.success(request, f'Beschikbaar op {target_date.strftime("%d %B")}!')
        return redirect('calendar')

    dinner_dates = {d.date: d for d in DinnerDate.objects.select_related('host').all()}
    scheduled_dates = set(dinner_dates.keys())

    all_avail = Availability.objects.select_related('couple').all()
    availability_map = {}
    my_available_dates = set()
    for a in all_avail:
        availability_map.setdefault(a.date, []).append(a.couple.name)
        if couple and a.couple == couple:
            my_available_dates.add(a.date)

    from django.db.models import Count
    proposed_count = (
        Availability.objects
        .values('date')
        .annotate(count=Count('couple'))
        .filter(count=total_couples, date__gte=today)
        .exclude(date__in=scheduled_dates)
        .count()
    )

    context = {
        'couple': couple,
        'month_data': [
            ('Juli', _build_month_grid(COMPETITION_YEAR, 7, dinner_dates, availability_map, my_available_dates, total_couples, couple, today)),
            ('Augustus', _build_month_grid(COMPETITION_YEAR, 8, dinner_dates, availability_map, my_available_dates, total_couples, couple, today)),
        ],
        'today': today,
        'year': COMPETITION_YEAR,
        'weekdays': ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'],
        'total_couples': total_couples,
        'proposed_count': proposed_count,
    }
    return render(request, 'dinner/calendar.html', context)


@login_required
def confirm_date_view(request):
    if request.user.username != 'florian_afra':
        messages.error(request, 'Alleen Florian & Afra kunnen een datum bevestigen.')
        return redirect('calendar')

    total_couples = Couple.objects.count()
    today = date.today()
    scheduled_dates = set(DinnerDate.objects.values_list('date', flat=True))

    from django.db.models import Count
    proposed_raw = (
        Availability.objects
        .values('date')
        .annotate(count=Count('couple'))
        .filter(count=total_couples, date__gte=today)
        .order_by('date')
    )

    proposed_dates = []
    for p in proposed_raw:
        d = p['date']
        if d not in scheduled_dates:
            available_couples = [a.couple for a in Availability.objects.filter(date=d).select_related('couple')]
            proposed_dates.append({'date': d, 'couples': available_couples})

    if request.method == 'POST':
        date_str = request.POST.get('date')
        host_id = request.POST.get('host')
        try:
            target_date = date.fromisoformat(date_str)
            host = Couple.objects.get(pk=host_id)
        except (ValueError, TypeError, Couple.DoesNotExist):
            messages.error(request, 'Ongeldige datum of koppel.')
            return redirect('confirm_date')

        if DinnerDate.objects.filter(date=target_date).exists():
            messages.error(request, 'Er is al een diner op die datum.')
        else:
            DinnerDate.objects.create(host=host, date=target_date)
            messages.success(request, f'Diner bevestigd op {target_date.strftime("%d %B")} — gastheer: {host.name}!')
        return redirect('calendar')

    return render(request, 'dinner/confirm_date.html', {
        'proposed_dates': proposed_dates,
        'couples': Couple.objects.all(),
        'couple': getattr(request.user, 'couple', None),
    })


@login_required
def dinner_detail(request, pk):
    dinner = get_object_or_404(DinnerDate, pk=pk)
    couple = request.user.couple
    today = date.today()
    is_host = dinner.host == couple
    is_past = dinner.date <= today
    teaser = getattr(dinner, 'teaser', None)

    can_score = not is_host and is_past
    existing_score = None
    score_form = None

    if can_score:
        existing_score = Score.objects.filter(dinner_date=dinner, scorer=couple).first()
        if request.method == 'POST':
            form = ScoreForm(request.POST, instance=existing_score)
            if form.is_valid():
                score = form.save(commit=False)
                score.dinner_date = dinner
                score.scorer = couple
                score.save()
                messages.success(request, 'Score ingediend!')
                return redirect('dinner_detail', pk=pk)
            score_form = form
        else:
            score_form = ScoreForm(instance=existing_score)

    aggregate = None
    if is_past:
        scores = dinner.scores.all()
        count = scores.count()
        if count:
            agg = scores.aggregate(
                food=Avg('food_score'),
                atm=Avg('atmosphere_score'),
                deco=Avg('decoration_score'),
            )
            aggregate = {
                'food': round(agg['food'], 1),
                'atmosphere': round(agg['atm'], 1),
                'decoration': round(agg['deco'], 1),
                'total': round((agg['food'] + agg['atm'] + agg['deco']), 1),
                'count': count,
            }

    context = {
        'dinner': dinner,
        'couple': couple,
        'is_host': is_host,
        'is_past': is_past,
        'teaser': teaser,
        'can_score': can_score,
        'existing_score': existing_score,
        'score_form': score_form,
        'aggregate': aggregate,
    }
    return render(request, 'dinner/dinner_detail.html', context)


@login_required
def menu_teaser_view(request, pk):
    dinner = get_object_or_404(DinnerDate, pk=pk)
    couple = request.user.couple

    if dinner.host != couple:
        messages.error(request, 'Alleen de gastheren kunnen de teaser bewerken.')
        return redirect('dinner_detail', pk=pk)

    teaser = getattr(dinner, 'teaser', None)

    if request.method == 'POST':
        form = MenuTeaserForm(request.POST, instance=teaser)
        if form.is_valid():
            t = form.save(commit=False)
            t.dinner_date = dinner
            t.save()
            messages.success(request, 'Menuteaser opgeslagen!')
            return redirect('home')
    else:
        form = MenuTeaserForm(instance=teaser)

    return render(request, 'dinner/menu_teaser.html', {'dinner': dinner, 'form': form, 'couple': couple})


@login_required
def leaderboard(request):
    all_couples = Couple.objects.all()
    try:
        current_couple = request.user.couple
    except Exception:
        current_couple = None
    today = date.today()
    rankings = []

    already_scored_ids = set(
        Score.objects.filter(scorer=current_couple).values_list('dinner_date_id', flat=True)
    ) if current_couple else set()

    for couple in all_couples:
        past_dinners = list(DinnerDate.objects.filter(host=couple, date__lte=today))
        scores = Score.objects.filter(dinner_date__in=past_dinners)
        count = scores.count()

        if count:
            agg = scores.aggregate(
                food=Sum('food_score'),
                atm=Sum('atmosphere_score'),
                deco=Sum('decoration_score'),
            )
            food_total = agg['food'] or 0
            atm_total = agg['atm'] or 0
            deco_total = agg['deco'] or 0
            grand_total = food_total + atm_total + deco_total
            avg_per_score = round(grand_total / count, 1)
        else:
            food_total = atm_total = deco_total = grand_total = 0
            avg_per_score = 0

        scorable = [
            d for d in past_dinners
            if couple != current_couple and d.pk not in already_scored_ids
        ]

        rankings.append({
            'couple': couple,
            'num_dinners': DinnerDate.objects.filter(host=couple).count(),
            'num_dinners_scored': len(past_dinners),
            'score_count': count,
            'food_total': food_total,
            'atm_total': atm_total,
            'deco_total': deco_total,
            'grand_total': grand_total,
            'avg_per_score': avg_per_score,
            'scorable_dinners': scorable,
        })

    rankings.sort(key=lambda x: x['grand_total'], reverse=True)
    for i, r in enumerate(rankings):
        r['rank'] = i + 1

    return render(request, 'dinner/leaderboard.html', {'rankings': rankings, 'couple': current_couple})

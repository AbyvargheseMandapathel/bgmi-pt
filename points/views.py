from django.db.models import OuterRef, Subquery
from django.shortcuts import render, redirect
from .models import Points, MatchResult, Team
from PIL import Image, ImageDraw, ImageFont
from django.http import HttpResponse
from django.db.models import Sum, Max, F
from django.db import IntegrityError
from django.http import HttpResponseServerError
from django.http import JsonResponse

def team_list(request):
    teams = Points.objects.all().order_by('-tp', '-pp', '-fp', '-wins')
    context = {'teams': teams}
    return render(request, 'team_list.html', context)

def download_image(request):
    # Open your image
    image_path = "template.jpg"
    image = Image.open(image_path).convert("RGBA")

    # Create a drawing context
    draw = ImageDraw.Draw(image)

    # Provide the path to your external font file
    font_path = "SCHABO-Condensed.otf"

    # Load the external font with the specified size and letter spacing
    font_size = 25
    letter_spacing = 16.8
    font = ImageFont.truetype(font_path, size=font_size)

    # Fetch and order teams by points as needed
    teams = Points.objects.order_by('-tp', '-pp', '-fp', '-wins')

    # Define the coordinates for team information
    coordinates = {
        'logo_x': 252,
        'logo_y': 444,
        'team_name_x': 331,
        'fp_x': 538,
        'pp_x': 646,
        'wins_x': 730,
        'tp_x': 824,
        'boundary_left': 252,
        'boundary_right': 316,
        'boundary_top': 444,
        'boundary_bottom': 498,
        'max_logo_width': 64,
        'max_logo_height': 54,
        'vertical_spacing': 58,
        'team_name_y': 460  # Initial position for the first team's name
    }

    # Calculate the number of matches for the day
    total_matches = Points.objects.aggregate(Sum('matches'))['matches__sum'] or 0

    # Display logos of the winning teams based on the match number
    last_six_matches = (
        MatchResult.objects
        .filter(matches__in=Subquery(
            MatchResult.objects.values('matches').order_by('-matches')[:6]
        ))
        .order_by('-matches')
    )

    # Define coordinates for the winning team posters
    poster_coordinates = {
        'left_x': 200,
        'left_top_y': 1390,
        'left_bottom_y': 1466,
        'right_x': 293
    }

    # Calculate the size of posters
    poster_width = poster_coordinates['right_x'] - poster_coordinates['left_x']
    poster_height = poster_coordinates['left_bottom_y'] - poster_coordinates['left_top_y']

    # Calculate the initial position for the first poster
    poster_x = poster_coordinates['left_x']
    poster_y_top = poster_coordinates['left_top_y']
    poster_y_bottom = poster_coordinates['left_bottom_y']

    # Determine the number of winning teams to display
    num_winning_teams = total_matches % 6

    # Check if num_winning_teams is 0 and set it to 6
    if num_winning_teams == 0:
        num_winning_teams = 6

    for match in last_six_matches[:num_winning_teams]:
        team = match.team
        # Load the team logo without converting it
        logo = Image.open(team.logo.path).convert("RGBA")

        # Ensure the output format is RGBA
        if logo.mode != 'RGBA':
            logo = logo.convert("RGBA")

        # Calculate the new dimensions to fit within the poster while maintaining aspect ratio
        width, height = logo.size
        aspect_ratio = width / height

        # Calculate the size to fit within the poster
        if width > poster_width:
            width = poster_width
            height = int(width / aspect_ratio)
        if height > poster_height:
            height = poster_height
            width = int(height * aspect_ratio)

        # Resize the logo to fit within the poster
        logo = logo.resize((width, height), Image.LANCZOS)

        # Calculate the position to center the logo within the poster
        x = poster_x + (poster_width - width) // 2
        y = poster_y_top + (poster_height - height) // 2

        # Paste the logo onto the image with transparency at the calculated position
        image.paste(logo, (x, y), logo)

        # Update the x-coordinate for the next poster
        poster_x += poster_width + 22  # Adding 22 for the gap between posters

    # Display team information
    for team in teams:
        # Load the team logo without converting it
        logo = Image.open(team.team.logo.path).convert("RGBA")

        # Ensure the output format is RGBA
        if logo.mode != 'RGBA':
            logo = logo.convert("RGBA")

        # Calculate the new dimensions to fit within the specified boundary while maintaining aspect ratio
        width, height = logo.size
        aspect_ratio = width / height

        # Check if the logo height is too close to the boundary (adjust the percentage as needed)
        min_allowed_height = coordinates['max_logo_height'] * 0.2
        if height > min_allowed_height:
            if width > coordinates['max_logo_width']:
                width = coordinates['max_logo_width']
                height = int(width / aspect_ratio)
            if height > coordinates['max_logo_height']:
                height = coordinates['max_logo_height']
                width = int(height * aspect_ratio)

        # Resize the logo to fit within the boundary
        logo = logo.resize((width, height), Image.LANCZOS)

        # Calculate the position to center the logo within the boundary
        x = coordinates['logo_x'] + (coordinates['max_logo_width'] - width) // 2
        y = coordinates['logo_y'] + (coordinates['max_logo_height'] - height) // 2

        # Paste the logo onto the image with transparency at the calculated position
        image.paste(logo, (x, y), logo)

        # Draw team name with letter spacing
        text = f"{team.team.name}"
        draw.text((coordinates['team_name_x'], coordinates['team_name_y']), text, fill="white", font=font, spacing=letter_spacing)

        # Draw other fields
        fields = ['fp', 'pp', 'wins', 'tp']
        for field in fields:
            x = coordinates[f'{field}_x']
            y = coordinates['team_name_y']
            text = f"{getattr(team, field)}"
            draw.text((x, y), text, fill="white", font=font, spacing=letter_spacing)

        # Increment the y-coordinate for vertical spacing
        coordinates['team_name_y'] += coordinates['vertical_spacing']
        coordinates['logo_y'] += coordinates['vertical_spacing']

    # Create an HttpResponse with image content
    response = HttpResponse(content_type="image/png")
    image.save(response, "PNG", quality=95)  # Maintain clarity with high quality

    # Set a filename for the downloaded image
    response["Content-Disposition"] = 'attachment; filename="team_standings.png"'

    return response

from django.db import IntegrityError

def add_points(request):
    if request.method == "POST":
        teams = Team.objects.all()
        num_teams = len(teams)

        # Create a list to store the input data for all teams
        team_data = []

        try:
            for i in range(1, num_teams + 1):
                team_id = request.POST.get(f"team_{i}")
                fp = request.POST.get(f"fp_{i}")
                pp = request.POST.get(f"pp_{i}")

                if team_id is not None and pp is not None and pp.strip():
                    team = Team.objects.get(id=team_id)
                    wins = 0

                    if pp == "15":
                        wins = 1

                    match_number = (
                        MatchResult.objects
                        .filter(team=team)
                        .aggregate(max_match_number=Max('matches'))['max_match_number'] or 0
                    )
                    match_number += 1

                    match_result = MatchResult(team=team, fp=fp, pp=pp, wins=wins, matches=match_number)
                    match_result.save()

                    team_data.append({'name': team.name, 'fp': fp, 'pp': pp})

        except IntegrityError as e:
            return HttpResponseServerError(f"Database error: {str(e)}")

        context = {'teams': Team.objects.all()}  # Retrieve all teams here
        return render(request, 'addpoints.html', context)

    context = {'teams': Team.objects.all()}  # Retrieve all teams here
    return render(request, 'addpoints.html', context)



def update_rankings(request):
    teams = Points.objects.all().order_by('-tp', '-pp', '-fp', '-wins')
    data = [{'team_name': team.team.name, 'tp': team.tp, 'pp': team.pp, 'fp': team.fp, 'wins': team.wins, 'logo_url': team.team.logo.url} for team in teams]
    return JsonResponse(data, safe=False)



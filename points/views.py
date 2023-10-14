from django.shortcuts import render
from .models import Points
from PIL import Image, ImageDraw, ImageFont
from django.http import HttpResponse
from django.db.models import Sum  # Import Sum


def team_list(request):
    teams = Points.objects.all().order_by('-tp', '-pp', '-fp', '-wins')
    context = {'teams': teams}
    return render(request, 'team_list.html', context)

def download_image(request):
    # Open your image
    image_path = "template.jpg"
    image = Image.open(image_path).convert("RGBA")  # Convert to RGBA mode

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

    total_matches = Points.objects.aggregate(Sum('matches'))['matches__sum']

    # Define coordinates for winning team posters
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

    for team in teams[:5]:  # Display logos of the previous 5 teams
        # Load the team logo without converting it
        logo = Image.open(team.team.logo.path).convert("RGBA")

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

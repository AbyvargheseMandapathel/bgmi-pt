from django.shortcuts import render
from .models import Points, Team
from PIL import Image, ImageDraw, ImageFont
from django.http import HttpResponse
from points.models import Points

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

    # Define the initial coordinates for the team logo and boundary
    logo_x, logo_y = 252, 444  # Initial position for the first team
    boundary_left = 252
    boundary_right = 316
    boundary_top = 444
    boundary_bottom = 498

    # Calculate the maximum allowable logo dimensions
    max_logo_width = boundary_right - boundary_left
    max_logo_height = boundary_bottom - boundary_top

    # Create spacing between teams
    vertical_spacing = 58

    for team in teams:
        # Load the team logo without converting it
        logo = Image.open(team.team.logo.path).convert("RGBA")  # Convert to RGBA mode

        # Ensure the output format is RGBA
        if logo.mode != 'RGBA':
            logo = logo.convert("RGBA")

        # Calculate the new dimensions to fit within the specified boundary while maintaining aspect ratio
        width, height = logo.size
        aspect_ratio = width / height

        # Check if the logo height is too close to the boundary (adjust the percentage as needed)
        min_allowed_height = max_logo_height * 0.2
        if height > min_allowed_height:
            if width > max_logo_width:
                width = max_logo_width
                height = int(width / aspect_ratio)
            if height > max_logo_height:
                height = max_logo_height
                width = int(height * aspect_ratio)

        # Resize the logo to fit within the boundary
        logo = logo.resize((width, height), Image.LANCZOS)

        # Calculate the position to center the logo within the boundary
        x, y = logo_x + (max_logo_width - width) // 2, logo_y + (max_logo_height - height) // 2

        # Paste the logo onto the image with transparency at the calculated position
        image.paste(logo, (x, y), logo)

        # Set the coordinates for the team name
        team_name_x = 331  # Fixed x-coordinate
        team_name_y = logo_y  # Team name at the same y-coordinate as the logo

        # Draw team name with letter spacing
        text = f"{team.team.name}"
        draw.text((team_name_x, team_name_y), text, fill="white", font=font, spacing=letter_spacing)
        
        # Increment the y-coordinate for vertical spacing
        team_name_y += vertical_spacing

        # Set the coordinates for other elements
        wins_x = 531
        other_elements_coords = (wins_x, logo_y)  # Wins, TP, PP, FP at the same y-coordinate as the logo

        # Draw other elements like Wins, TP, PP, FP
        elements = [f"{team.wins}", f"{team.tp}", f"{team.pp}", f"{team.fp}"]
        for element in elements:
            draw.text(other_elements_coords, element, fill="white", font=font, spacing=letter_spacing)
            other_elements_coords = (other_elements_coords[0] + 150, other_elements_coords[1])  # Adjust x-coordinate for the next element

        # Update the y-coordinate for the next team (58 pixels below the current one)
        logo_y += vertical_spacing

    # Create an HttpResponse with image content
    response = HttpResponse(content_type="image/png")
    image.save(response, "PNG", quality=95)  # Maintain clarity with high quality

    # Set a filename for the downloaded image
    response["Content-Disposition"] = 'attachment; filename="team_standings.png"'

    return response

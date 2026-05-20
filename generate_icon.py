"""
Generate a simple icon for the Lot Plotter plugin.
Run this once to create the icon.png file.
"""

try:
    from PIL import Image, ImageDraw
    
    # Create a new image (256x256)
    img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a simple lot/polygon shape
    # Draw background circle
    draw.ellipse([20, 20, 236, 236], fill=(100, 150, 200, 255), outline=(50, 100, 150, 255), width=3)
    
    # Draw a quadrilateral (lot shape) inside
    points = [(80, 80), (176, 80), (176, 176), (80, 176), (80, 80)]
    draw.polygon(points[:-1], fill=(150, 200, 100, 200), outline=(100, 150, 50, 255), width=2)
    
    # Add corner markers
    corner_size = 6
    for x, y in points[:-1]:
        draw.ellipse([x-corner_size, y-corner_size, x+corner_size, y+corner_size], 
                     fill=(255, 100, 0, 255))
    
    # Save the image
    icon_path = __file__.replace('generate_icon.py', 'icon.png')
    img.save(icon_path)
    print(f"Icon created at: {icon_path}")
    
except ImportError:
    print("PIL not installed. Creating icon manually...")
    # If PIL is not available, we'll just note this in the plugin
    pass

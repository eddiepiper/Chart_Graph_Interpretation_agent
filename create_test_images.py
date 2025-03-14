from PIL import Image, ImageDraw
import os

def create_line_chart(width, height):
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw border
    draw.rectangle([0, 0, width-1, height-1], outline='black')
    
    # Draw axes
    draw.line([(50, 350), (50, 50)], fill='black', width=2)  # Y-axis
    draw.line([(50, 350), (550, 350)], fill='black', width=2)  # X-axis
    
    # Draw line chart
    points = [(50, 350), (150, 200), (250, 300), (350, 150), (450, 250)]
    for i in range(len(points)-1):
        draw.line([points[i], points[i+1]], fill='blue', width=2)
    
    # Add title
    draw.text((width//2-50, 20), "Test Line Chart", fill='black')
    
    return img

def create_bar_chart(width, height):
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw border
    draw.rectangle([0, 0, width-1, height-1], outline='black')
    
    # Draw axes
    draw.line([(50, 350), (50, 50)], fill='black', width=2)  # Y-axis
    draw.line([(50, 350), (550, 350)], fill='black', width=2)  # X-axis
    
    # Draw bars
    bar_positions = [(100, 100), (200, 150), (300, 200), (400, 120)]
    for x, h in bar_positions:
        draw.rectangle([x, 350-h, x+40, 350], fill='blue')
    
    # Add title
    draw.text((width//2-50, 20), "Test Bar Chart", fill='black')
    
    return img

def main():
    # Create test_images directory if it doesn't exist
    os.makedirs("test_images", exist_ok=True)
    
    # Create and save line chart
    line_chart = create_line_chart(600, 400)
    line_chart.save("test_images/line_chart.png")
    
    # Create and save bar chart
    bar_chart = create_bar_chart(600, 400)
    bar_chart.save("test_images/bar_chart.png")
    
    # Create a small logo (non-chart image)
    logo = Image.new('RGB', (50, 50), 'lightgray')
    draw = ImageDraw.Draw(logo)
    draw.text((10, 20), "LOGO", fill='black')
    logo.save("test_images/logo.png")

if __name__ == "__main__":
    main()
    print("Test images created successfully!") 
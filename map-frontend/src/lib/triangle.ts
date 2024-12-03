const width = 50;
const height = 50;
const triangle = new ImageData(width, height);

// Loop through only the first row and first column to set them to black
for (let x = 0; x < width; x++) {
    // Set black pixel in the first row (y = 0)
    const index = x * 4;
    triangle.data[index] = 0;        // Red
    triangle.data[index + 1] = 0;    // Green
    triangle.data[index + 2] = 0;    // Blue
    triangle.data[index + 3] = 255;  // Alpha (opaque)
}

for (let y = 0; y < height; y++) {
    // Set black pixel in the first column (x = 0)
    const index = y * width * 4;
    triangle.data[index] = 0;        // Red
    triangle.data[index + 1] = 0;    // Green
    triangle.data[index + 2] = 0;    // Blue
    triangle.data[index + 3] = 255;  // Alpha (opaque)
}

export default triangle;
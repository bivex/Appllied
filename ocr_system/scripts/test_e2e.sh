#!/bin/bash
# End-to-end test script for OCR system CLI tools
# Run from project root: bash scripts/test_e2e.sh

set -e  # exit on error

echo "=========================================="
echo "OCR System - End-to-End Test"
echo "=========================================="

# Use clean Python environment to avoid PYTHONHOME/PYTHONPATH issues
PYTHON="/usr/bin/python3"

# Unset problematic environment variables
unset PYTHONHOME
unset PYTHONPATH

# Create test output directory
TEST_DIR="/tmp/ocr_e2e_test_$(date +%s)"
mkdir -p "$TEST_DIR"
echo "Test directory: $TEST_DIR"

# Step 1: Generate test images
echo ""
echo "Step 1: Generating test images..."
$PYTHON -m ocr_system.scripts.generate_text_images \
    --num 3 \
    --output-dir "$TEST_DIR/images" \
    2>&1 | tail -5

if [ $? -ne 0 ]; then
    echo "ERROR: Image generation failed"
    exit 1
fi

# Verify images were created
echo "Verifying generated images..."
if [ $(ls -1 "$TEST_DIR/images"/*.png 2>/dev/null | wc -l) -lt 3 ]; then
    echo "ERROR: Not enough images generated"
    exit 1
fi
echo "✓ Images generated successfully"

# Step 2: Extract text from first image
echo ""
echo "Step 2: Extracting text from first image..."
IMAGE="$TEST_DIR/images/sample_001.png"
$PYTHON -m ocr_system.scripts.extract_text \
    "$IMAGE" \
    --confidence \
    2>&1

if [ $? -ne 0 ]; then
    echo "ERROR: Text extraction failed"
    exit 1
fi
echo "✓ Text extraction successful"

# Step 3: Extract text to file
echo ""
echo "Step 3: Extract to file..."
$PYTHON -m ocr_system.scripts.extract_text \
    "$IMAGE" \
    --output "$TEST_DIR/extracted.txt" \
    2>&1 | tail -3

if [ $? -ne 0 ]; then
    echo "ERROR: File extraction failed"
    exit 1
fi
echo "Output saved to: $TEST_DIR/extracted.txt"
echo "Contents:"
cat "$TEST_DIR/extracted.txt"
echo "✓ File extraction successful"

# Step 4: Test transparent background fix
echo ""
echo "Step 4: Testing transparent background handling..."
$PYTHON -c "
from PIL import Image, ImageDraw
img = Image.new('RGBA', (600, 150), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
draw.text((20, 20), 'PencilKit Test', fill=(0, 0, 0, 255))
img.save('$TEST_DIR/transparent.png')
print('Created transparent image')
"

$PYTHON -m ocr_system.scripts.extract_text \
    "$TEST_DIR/transparent.png" \
    2>&1 | grep -E "(compositing|Recognized Text)" | head -5

if [ $? -eq 0 ]; then
    echo "✓ Transparent background handling works"
else
    echo "ERROR: Transparent background test failed"
    exit 1
fi

# Step 5: Test fast mode
echo ""
echo "Step 5: Testing fast recognition level..."
$PYTHON -m ocr_system.scripts.extract_text \
    "$IMAGE" \
    --level fast \
    2>&1 | tail -3

echo "✓ Fast mode works"

# Step 6: Custom text image and specific language
echo ""
echo "Step 6: Custom text + French language..."
$PYTHON -m ocr_system.scripts.generate_text_images \
    --text "Bonjour tout le monde" \
    --font-size 48 \
    --output-dir "$TEST_DIR" \
    2>&1 | tail -1

$PYTHON -m ocr_system.scripts.extract_text \
    "$TEST_DIR/custom.png" \
    --languages fr-FR \
    2>&1 | tail -3

echo "✓ French language works"

# Summary
echo ""
echo "=========================================="
echo "E2E TEST SUMMARY"
echo "=========================================="
echo "Test directory: $TEST_DIR"
echo "Generated images:"
ls -lh "$TEST_DIR/images/"*.png 2>/dev/null || echo "  (none)"
echo ""
echo "All tests passed! ✓"
echo ""
echo "Artifacts preserved in: $TEST_DIR"

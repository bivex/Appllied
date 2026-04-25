# Vision OCR with PencilKit - Common Pitfalls & Solutions

## Problem: "No text recognized" from PencilKit drawings

When using `VNRecognizeTextRequest` with images generated from `PKCanvasView` or `PKDrawing`, Vision often returns no text even though the drawing clearly contains text.

### Root Cause

`PKDrawing` renders with a **transparent background** by default. When this image (with alpha channel) is passed to Vision:

- Transparent pixels are interpreted as **black**
- Black strokes on a "perceived black" background have **zero contrast**
- The text detector fails to find character/line regions
- Result: "No text recognized"

This is why changing stroke color to red (or any non-black) appears to work — red has contrast against the interpreted black background.

### Solution: Composite onto White Background

Before passing the image to Vision, render the drawing onto an opaque white background:

#### Swift (iOS/macOS)

```swift
func recognizeTextFromDrawing() {
    guard !canvasView.drawing.strokes.isEmpty else { return }

    let drawing = canvasView.drawing
    let bounds = drawing.bounds.insetBy(dx: -10, dy: -10)  // add margin

    // CRITICAL: Composite onto white background
    let renderer = UIGraphicsImageRenderer(size: bounds.size)
    let compositedImage = renderer.image { ctx in
        // Fill with white (or any light color)
        UIColor.white.setFill()
        ctx.fill(bounds)

        // Draw the PencilKit strokes on top
        drawing.draw(in: bounds)
    }

    guard let cgImage = compositedImage.cgImage else { return }

    let request = VNRecognizeTextRequest { request, error in
        // ... handle results
    }

    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["en-US"]

    // For handwritten text, adjust for iOS 16+:
    if #available(iOS 16.0, *) {
        request.revision = VNRecognizeTextRequestRevision3
        request.automaticallyDetectsLanguage = false
    }

    let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    DispatchQueue.global(qos: .userInitiated).async {
        try? handler.perform([request])
    }
}
```

#### Objective-C / PyObjC (Python)

```python
# In PyObjC, use UIKit/UIGraphics to composite
from UIKit import UIGraphicsImageRenderer, UIColor

def composite_drawing_to_white(drawing, bounds):
    renderer = UIGraphicsImageRenderer.alloc().initWithSize_(bounds.size)
    composited = renderer.imageWithActions_(
        lambda ctx: (
            UIColor.whiteColor().setFill(),
            ctx.fill(bounds),
            drawing.drawInRect_(bounds)
        )
    )
    return composited
```

### Alternative: Change Stroke Color

As a quick workaround, use red, blue, or any non-black stroke color. However, this changes the user experience and isn't suitable for most apps (Notes uses black ink, so they definitely composite onto white).

### Additional Tips for Handwriting Recognition

1. **Use `.accurate` recognition level** (not `.fast`)
2. **Set revision to 3** on iOS 16+ (`VNRecognizeTextRequestRevision3`)
3. **Disable auto-detect language** if you know the language
4. **Add custom words** if your app uses domain-specific terminology:
   ```swift
   request.customWords = ["appName", "specificTerm"]
   ```
5. **Scale matters**: Use `scale: 3.0` or higher when creating the image for better results
6. **Margins**: Inset bounds by -10 to -20 points to avoid cutting off ascenders/descenders

### Complete Swift Example

```swift
import SwiftUI
import PencilKit
import Vision

struct HandwritingRecognizerView: View {
    @State private var canvasView = PKCanvasView()
    @State private var recognizedText = ""

    var body: some View {
        VStack {
            PencilKitCanvasRepresentable(canvasView: $canvasView)
                .frame(height: 300)

            Button("Recognize") {
                recognizeHandwriting()
            }

            Text(recognizedText)
                .padding()
        }
    }

    func recognizeHandwriting() {
        let drawing = canvasView.drawing
        guard !drawing.strokes.isEmpty else { return }

        let bounds = drawing.bounds.insetBy(dx: -20, dy: -20)

        // Composite onto white
        let renderer = UIGraphicsImageRenderer(size: bounds.size)
        let image = renderer.image { ctx in
            UIColor.white.setFill()
            ctx.fill(CGRect(origin: .zero, size: bounds.size))
            drawing.draw(in: bounds)
        }

        guard let cgImage = image.cgImage else { return }

        let request = VNRecognizeTextRequest { request, error in
            guard let observations = request.results as? [VNRecognizedTextObservation] else {
                return
            }
            let text = observations.compactMap {
                $0.topCandidates(1).first?.string
            }.joined(separator: " ")
            DispatchQueue.main.async {
                self.recognizedText = text
            }
        }

        request.recognitionLevel = .accurate
        request.recognitionLanguages = ["en-US"]
        if #available(iOS 16.0, *) {
            request.revision = VNRecognizeTextRequestRevision3
            request.automaticallyDetectsLanguage = false
        }

        let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
        DispatchQueue.global(qos: .userInitiated).async {
            try? handler.perform([request])
        }
    }
}
```

### References

- [Apple Vision Documentation](https://developer.apple.com/documentation/vision)
- [PencilKit Documentation](https://developer.apple.com/documentation/pencilkit)
- WWDC 2022/2023: Advances in Text Recognition
- Stack Overflow: [Text recognition with VNRecognizeTextRequest not working](https://stackoverflow.com/questions/...)

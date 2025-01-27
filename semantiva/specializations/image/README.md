# Gaussian Image Processing with Semantiva

This README demonstrates how to **generate, manipulate, visualize, and verify 2D Gaussian images** using **Semantiva's image processing framework**.

## 🚀 Features Covered:
- **Generate** 2D Gaussian images with `TwoDGaussianImageGenerator`
- **Stack images** into `ImageStackDataType`
- **Apply transformations**:
  - Mean projection (`StackToImageMeanProjector`)
  - Side-by-side projection (`ImageStackToSideBySideProjector`)
- **Verify Gaussian properties** with `TwoDGaussianFitterProbe`

---

## Full Example

```python
import matplotlib.pyplot as plt
from semantiva.specializations.image.image_loaders_savers_generators import TwoDGaussianImageGenerator
from semantiva.specializations.image.image_data_types import ImageStackDataType
from semantiva.specializations.image.image_algorithms import (
    StackToImageMeanProjector,
    ImageStackToSideBySideProjector,
)
from semantiva.specializations.image.image_probes import TwoDGaussianFitterProbe

# Step 1: Generate Gaussian Images using the updated interface
generator = TwoDGaussianImageGenerator()

image1 = generator._get_data(center=(512, 512), std_dev=40, amplitude=100, image_size=(1024, 1024))
image2 = generator._get_data(center=(550, 550), std_dev=40, amplitude=100, image_size=(1024, 1024))
image3 = generator._get_data(center=(580, 580), std_dev=40, amplitude=100, image_size=(1024, 1024))

# Step 2: Display the Generated Images
for idx, image in enumerate([image1, image2, image3], start=1):
    plt.imshow(image.data, cmap='hot')
    plt.title(f"Generated Image {idx}")
    plt.colorbar()
    plt.show()

# Step 3: Construct an Image Stack
image_stack = ImageStackDataType.from_list([image1, image2, image3])


# Step 4: Apply Image Processing Algorithms

# 4.1: Compute the mean projection of the stack
mean_projector = StackToImageMeanProjector()
flattened_image = mean_projector.process(image_stack)

# Display the mean-projected image
plt.imshow(flattened_image.data, cmap='hot')
plt.title("Flattened Image (Mean Projection)")
plt.colorbar()
plt.show()

# 4.2: Concatenate images horizontally
side_by_side_projector = ImageStackToSideBySideProjector()
side_by_side_image = side_by_side_projector.process(image_stack)

# Display the side-by-side image
plt.imshow(side_by_side_image.data, cmap='hot')
plt.title("Side by Side Image")
plt.colorbar()
plt.show()

# Step 5: Verify the Generated Images using TwoDGaussianFitterProbe
fitter_probe = TwoDGaussianFitterProbe()

for idx, image in enumerate([image1, image2, image3], start=1):
    fitted_params = fitter_probe.process(image)
    
    # Display fitted parameters
    print(f"Fitted Parameters for Image {idx}:")
    print(f" - Peak Center: {fitted_params['peak_center']}")
    print(f" - Amplitude: {fitted_params['amplitude']}")
    print(f" - Std Dev X: {fitted_params['std_dev_x']}")
    print(f" - Std Dev Y: {fitted_params['std_dev_y']}")
    print(f" - R-Squared: {fitted_params['r_squared']}\n")
```


import pytest
import numpy as np
from semantiva.specializations.image.image_data_types import ImageStackDataType
from semantiva.specializations.image.image_viewers import ImageStackAnimator


# Sample test data
@pytest.fixture
def test_image_stack():
    """Fixture to provide test image stack data."""
    return ImageStackDataType(np.random.rand(10, 256, 256))


def test_display_animation(test_image_stack):
    """Test that the animation is correctly displayed."""
    ImageStackAnimator.view(test_image_stack)

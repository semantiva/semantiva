import pytest
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from semantiva.specializations.image.image_viewers import ImageViewer
from semantiva.specializations.image.image_data_types import ImageDataType


@pytest.fixture
def test_image():
    """Fixture to provide test image data."""
    return ImageDataType(data=np.random.rand(10, 10))


def test_generate_image(test_image):
    """Test if _generate_image() creates a valid figure."""
    fig = ImageViewer._generate_image(
        test_image,
        title="Test",
        colorbar=True,
        cmap="plasma",
        log_scale=True,
        xlabel="X",
        ylabel="Y",
    )

    assert isinstance(fig, plt.Figure)  # Ensure a matplotlib Figure is returned
    assert len(fig.axes) > 0  # Ensure the figure has at least one axis

    ax = fig.axes[0]  # Get the first axis
    assert ax.get_title() == "Test"  # Check title
    assert ax.get_xlabel() == "X"  # Check x-axis label
    assert ax.get_ylabel() == "Y"  # Check y-axis label

    # Check colormap
    assert ax.images[0].get_cmap().name == "plasma"

    # Check if log scale is applied
    assert isinstance(ax.images[0].norm, LogNorm)


def test_display_image(monkeypatch, test_image):
    """Test if display_image() calls plt.show()"""

    # Use monkeypatch to replace plt.show() with a dummy function
    show_called = []

    def mock_show():
        show_called.append(True)

    monkeypatch.setattr(plt, "show", mock_show)

    ImageViewer.view(test_image)

    # Verify that plt.show() was called
    assert show_called, "plt.show() was not called"

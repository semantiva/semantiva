import pytest
import numpy as np
import matplotlib.pyplot as plt
from ipywidgets import Checkbox, Dropdown, FloatSlider, Text
from semantiva.specializations.image.image_viewers import (
    ImageInteractiveViewer,
    ImageCrossSectionInteractiveViewer,
    ImageXYProjectionViewer,
)
from semantiva.specializations.image.image_data_types import ImageDataType


# Sample test data
@pytest.fixture
def test_image():
    """Fixture to provide test image data."""
    return ImageDataType(np.random.rand(256, 256))


def test_figure_options():
    """Ensure FIGURE_OPTIONS has correct types and values."""
    options = ImageInteractiveViewer.FIGURE_OPTIONS

    assert "Small (500x400)" in options
    assert "Medium (700x500)" in options
    assert "Large (1000x800)" in options


def test_generate_widgets(test_image):
    """Test that interactive widgets are correctly created."""
    viewer = ImageInteractiveViewer()

    # Create widgets
    colorbar_widget = Checkbox(value=False, description="Colorbar")
    log_scale_widget = Checkbox(value=False, description="Log Scale")
    cmap_widget = Dropdown(
        options=["viridis", "plasma", "gray", "magma", "hot"],
        value="viridis",
        description="Colormap:",
    )
    vmin_widget = FloatSlider(
        value=1e-2,
        min=1e-2,
        max=float(test_image.data.max()),
        step=0.1,
        description="vmin",
    )
    vmax_widget = FloatSlider(
        value=float(test_image.data.max()),
        min=1e-2,
        max=float(test_image.data.max()),
        step=0.1,
        description="vmax",
    )
    title_widget = Text(value="", description="Title:")
    xlabel_widget = Text(value="", description="X Label:")
    ylabel_widget = Text(value="", description="Y Label:")
    figure_size_widget = Dropdown(
        options=list(viewer.FIGURE_OPTIONS.keys()),
        value=list(viewer.FIGURE_OPTIONS.keys())[1],
        description="Figure Size:",
    )

    # Ensure widgets have the correct properties
    assert isinstance(colorbar_widget, Checkbox)
    assert isinstance(log_scale_widget, Checkbox)
    assert isinstance(cmap_widget, Dropdown)
    assert isinstance(vmin_widget, FloatSlider)
    assert isinstance(vmax_widget, FloatSlider)
    assert isinstance(title_widget, Text)
    assert isinstance(xlabel_widget, Text)
    assert isinstance(ylabel_widget, Text)
    assert isinstance(figure_size_widget, Dropdown)


def test_update_plot(monkeypatch, test_image):
    """Test if update_plot() runs without errors and calls plt.show()."""

    # Mock plt.show() to avoid opening a figure window
    show_called = []

    def mock_show():
        show_called.append(True)

    monkeypatch.setattr(plt, "show", mock_show)

    # Call update_plot with dummy values
    ImageInteractiveViewer._update_plot(
        test_image,
        colorbar=True,
        log_scale=True,
        cmap="plasma",
        vmin=0.1,
        vmax=1.0,
        title="Test Plot",
        xlabel="X Axis",
        ylabel="Y Axis",
        figure_size="Medium (700x500)",
    )

    # Ensure plt.show() was called
    assert show_called, "plt.show() was not called"


def test_cross_sec_interactive_viewer(test_image):
    """Test that CrossSecInteractiveViewer can be instantiated.
    with no errors."""
    viewer = ImageCrossSectionInteractiveViewer.view(test_image)

    assert isinstance(viewer, ImageCrossSectionInteractiveViewer)


def test_xy_projection_viewer(test_image):
    """Test that XYProjectionViewer can be instantiated.
    with no errors."""
    viewer = ImageXYProjectionViewer.view(test_image)

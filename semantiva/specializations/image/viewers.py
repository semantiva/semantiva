import ipywidgets as widgets
from IPython.display import display, HTML
from matplotlib.colors import LogNorm
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from semantiva.specializations.image.image_data_types import (
    ImageDataType,
    ImageStackDataType,
)


class ImageViewer:
    """
    A concrete implementation that processes an image with customizable settings.
    """

    @classmethod
    def display_image(
        cls,
        data: ImageDataType,
        title: str = "",
        colorbar: bool = False,
        cmap: str = "viridis",
        log_scale: bool = False,
    ):
        """Display an image with optional title, colorbar, colormap, and log scale."""
        figure = cls._generate_image(
            data, title=title, colorbar=colorbar, cmap=cmap, log_scale=log_scale
        )
        figure.show()

    @classmethod
    def _generate_image(
        cls,
        data: ImageDataType,
        title: str = "",
        colorbar: bool = False,
        cmap: str = "viridis",
        log_scale: bool = False,
    ) -> Figure:
        """Generate figure with the image"""
        norm = None
        fig = plt.figure()
        plt.title(title)
        if log_scale:
            norm = LogNorm(vmin=1e-2, vmax=data.data.max())
        plt.imshow(data.data, cmap=cmap, norm=norm)
        if colorbar:
            plt.colorbar()
        return fig


class ImageInteractiveViewer(ImageViewer):
    """
    An extension of ImageViewer that supports interactivity in Jupyter Notebook.
    """

    @classmethod
    def interactive_generate_image(
        cls,
        data: ImageDataType,
        title: str = "",
        colorbar: bool = False,
        cmap: str = "viridis",
        log_scale: bool = False,
    ):
        """Create an interactive image viewer with ipywidgets."""

        # Widgets
        colorbar_widget = widgets.Checkbox(value=colorbar, description="Colorbar")
        log_scale_widget = widgets.Checkbox(value=log_scale, description="Log Scale")
        cmap_widget = widgets.Dropdown(
            options=["viridis", "plasma", "gray", "magma", "hot"],
            value=cmap,
            description="Colormap:",
        )

        vmin_widget = widgets.FloatSlider(
            value=1e-2, min=1e-2, max=data.data.max(), step=0.1, description="vmin"
        )
        vmax_widget = widgets.FloatSlider(
            value=data.data.max(),
            min=1e-2,
            max=data.data.max(),
            step=0.1,
            description="vmax",
        )

        # Ensure vmax is always greater than vmin
        def update_vmax_range(change):
            if vmax_widget.value <= vmin_widget.value:
                vmax_widget.value = vmin_widget.value + 0.1

        def update_vmin_range(change):
            if vmin_widget.value >= vmax_widget.value:
                vmin_widget.value = vmax_widget.value - 0.1

        vmin_widget.observe(update_vmax_range, names="value")
        vmax_widget.observe(update_vmin_range, names="value")

        vmin_widget.observe(update_vmax_range, names="value")
        # Create figure and axes

        def update_plot(colorbar, log_scale, cmap, vmin, vmax):
            """Update plot based on widget values."""
            plt.figure(figsize=(6, 4))
            norm = LogNorm(vmin=vmin, vmax=vmax) if log_scale else None
            plt.imshow(data.data, cmap=cmap, norm=norm)
            plt.title(title)
            if colorbar:
                plt.colorbar()
            plt.show()

        # Bind widgets to the plotting function
        interactive_plot = widgets.interactive(
            update_plot,
            colorbar=colorbar_widget,
            log_scale=log_scale_widget,
            cmap=cmap_widget,
            vmin=vmin_widget,
            vmax=vmax_widget,
        )

        # Display the interactive plot
        display(interactive_plot)


class ImageStackAnimator:
    """
    A concrete implementation that processes an image stack into an animation.

    The generated animation cycles through each image in the stack, allowing visualization of
    dynamic or sequential image data.
    """

    @classmethod
    def display_animation(
        cls, image_stack: ImageStackDataType, frame_duration: int = 200
    ):
        """
        Creates and displays an animation using matplotlib.animation.

        Parameters:
            image_stack (ImageStackDataType): Stack of images to animate.
        """
        fig, ax = plt.subplots()
        frames = []

        for img in image_stack.data:
            img_array = np.array(img.data)
            img_normalized = (
                (img_array - img_array.min())
                * 255
                / (img_array.max() - img_array.min())
            ).astype(np.uint8)
            frame = ax.imshow(img_normalized, cmap="hot", animated=True)
            frames.append([frame])

        ani = animation.ArtistAnimation(fig, frames, interval=frame_duration, blit=True)

        # Display the animation
        display(HTML(ani.to_jshtml()))
        plt.close()

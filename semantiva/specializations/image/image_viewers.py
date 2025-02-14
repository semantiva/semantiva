import numpy as np
import ipywidgets as widgets
from typing import TypedDict
from IPython.display import display, HTML
from matplotlib.colors import LogNorm
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.widgets import Slider, Button, RadioButtons, CheckButtons
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import LogNorm
from semantiva.specializations.image.image_data_types import (
    ImageDataType,
    ImageStackDataType,
)


class FigureOption(TypedDict):
    figsize: tuple[float, float]
    labelsize: int


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
        xlabel: str = "",
        ylabel: str = "",
    ):
        """Display an image with optional title, colorbar, colormap, and log scale."""
        figure = cls._generate_image(
            data,
            title=title,
            colorbar=colorbar,
            cmap=cmap,
            log_scale=log_scale,
            xlabel=xlabel,
            ylabel=ylabel,
        )
        plt.show()

    @classmethod
    def _generate_image(
        cls,
        data: ImageDataType,
        title: str = "",
        colorbar: bool = False,
        cmap: str = "viridis",
        log_scale: bool = False,
        xlabel: str = "",
        ylabel: str = "",
    ) -> Figure:
        """Generate figure with the image"""
        norm = None
        fig = plt.figure()
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
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

    FIGURE_OPTIONS: dict[str, FigureOption] = {
        "Small (500x400)": {"figsize": (5, 4), "labelsize": 10},
        "Medium (700x500)": {"figsize": (7, 5), "labelsize": 12},
        "Large (1000x800)": {"figsize": (10, 8), "labelsize": 14},
    }

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
        title_widget = widgets.Text(value=title, description="Title:")
        xlabel_widget = widgets.Text(value="", description="X Label:")
        ylabel_widget = widgets.Text(value="", description="Y Label:")

        figure_size_widget = widgets.Dropdown(
            options=list(cls.FIGURE_OPTIONS.keys()),
            value="Medium (700x500)",
            description="Figure Size:",
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

        # Bind widgets to the plotting function
        interactive_plot = widgets.interactive(
            cls.update_plot,
            data=widgets.fixed(data),
            colorbar=colorbar_widget,
            log_scale=log_scale_widget,
            cmap=cmap_widget,
            vmin=vmin_widget,
            vmax=vmax_widget,
            title=title_widget,
            xlabel=xlabel_widget,
            ylabel=ylabel_widget,
            figure_size=figure_size_widget,
        )

        # Display the interactive plot
        display(interactive_plot)

    @classmethod
    def update_plot(
        cls,
        data: ImageDataType,
        colorbar: bool,
        log_scale: bool,
        cmap: str,
        vmin: float,
        vmax: float,
        title: str,
        xlabel: str,
        ylabel: str,
        figure_size: str,
    ):
        """Update plot based on widget values."""
        fig_options = cls.FIGURE_OPTIONS[figure_size]
        figsize = fig_options["figsize"]
        labelsize = fig_options["labelsize"]

        plt.figure(figsize=figsize)
        norm = LogNorm(vmin=vmin, vmax=vmax) if log_scale else None
        plt.imshow(data.data, cmap=cmap, norm=norm)
        plt.title(title, fontsize=labelsize + 2)
        plt.xlabel(xlabel, fontsize=labelsize)
        plt.ylabel(ylabel, fontsize=labelsize)
        plt.xticks(fontsize=labelsize - 2)
        plt.yticks(fontsize=labelsize - 2)
        if colorbar:
            plt.colorbar()
        plt.show()


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


class ImageCrossSectionInteractiveViewer:
    def __init__(self, image_data):
        self.image_data = image_data.data
        self.ny, self.nx = self.image_data.shape
        self.cur_x = self.nx // 2
        self.cur_y = self.ny // 2
        self.z_max = self.image_data.max()
        self.z_min = self.image_data.min()
        self.cmap = "hot"
        self.log_scale = False
        self.auto_scale = False

        self.fig, self.main_ax = plt.subplots(figsize=(7, 7))
        self.fig.subplots_adjust(top=0.85, bottom=0.2)

        divider = make_axes_locatable(self.main_ax)
        self.top_ax = divider.append_axes("top", 1.05, pad=0.1, sharex=self.main_ax)
        self.right_ax = divider.append_axes("right", 1.05, pad=0.1, sharey=self.main_ax)

        self.top_ax.xaxis.set_tick_params(labelbottom=False)
        self.right_ax.yaxis.set_tick_params(labelleft=False)

        self.update_norm()

        self.img = self.main_ax.imshow(
            self.image_data, origin="lower", cmap=self.cmap, norm=self.norm
        )
        self.colorbar = self.fig.colorbar(
            self.img, ax=self.main_ax, orientation="vertical", shrink=0.8
        )

        self.main_ax.autoscale(enable=False)
        self.right_ax.autoscale(enable=False)
        self.top_ax.autoscale(enable=False)

        (self.v_line,) = self.main_ax.plot([self.cur_x, self.cur_x], [0, self.ny], "r-")
        (self.h_line,) = self.main_ax.plot([0, self.nx], [self.cur_y, self.cur_y], "g-")

        (self.v_prof,) = self.right_ax.plot(
            self.image_data[:, self.cur_x], np.arange(self.ny), "r-"
        )
        (self.h_prof,) = self.top_ax.plot(
            np.arange(self.nx), self.image_data[self.cur_y, :], "g-"
        )

        self.fig.canvas.mpl_connect("button_press_event", self.on_click)
        self.create_widgets()
        self.update_profiles()

    def update_norm(self):
        if self.log_scale:
            positive_values = self.image_data[self.image_data > 0]
            vmin = (
                max(positive_values.min(), 1e-3) if positive_values.size > 0 else 1e-3
            )
            self.norm = LogNorm(vmin=vmin, vmax=self.z_max)
        else:
            self.norm = None

    def update_cross_section(self, val=None):
        self.cur_x = int(self.x_slider.val)
        self.cur_y = int(self.y_slider.val)
        self.cur_x = np.clip(self.cur_x, 0, self.nx - 1)
        self.cur_y = np.clip(self.cur_y, 0, self.ny - 1)

        self.v_line.set_data([self.cur_x, self.cur_x], [0, self.ny])
        self.h_line.set_data([0, self.nx], [self.cur_y, self.cur_y])

        self.update_profiles()
        self.img.set_data(self.image_data)
        self.fig.canvas.draw_idle()

    def update_profiles(self):
        v_prof_data = self.image_data[:, self.cur_x]
        h_prof_data = self.image_data[self.cur_y, :]

        margin = 0.05  # 5% margin for better visualization

        if self.auto_scale:
            v_min, v_max = v_prof_data.min(), v_prof_data.max()
            h_min, h_max = h_prof_data.min(), h_prof_data.max()

            v_range = v_max - v_min
            h_range = h_max - h_min

            v_min -= v_range * margin
            v_max += v_range * margin
            h_min -= h_range * margin
            h_max += h_range * margin
        else:
            v_min, v_max = self.z_min, self.z_max
            h_min, h_max = self.z_min, self.z_max

        # Ensure positive limits for log scale
        if self.log_scale:
            v_min = max(v_min, 1e-3)  # Avoid non-positive values
            h_min = max(h_min, 1e-3)

        # Update axes limits
        self.right_ax.set_xlim(v_min, v_max)
        self.v_prof.set_data(np.arange(self.ny), v_prof_data)
        self.top_ax.set_ylim(h_min, h_max)
        self.h_prof.set_data(np.arange(self.nx), h_prof_data)

        self.v_prof.set_data(v_prof_data, np.arange(self.ny))
        self.h_prof.set_data(np.arange(self.nx), h_prof_data)

        self.fig.canvas.draw_idle()

    def toggle_logscale(self, label):
        if label == "Log Scale":
            self.log_scale = not self.log_scale
            self.update_norm()
            self.img.set_norm(self.norm)
            self.colorbar.update_normal(self.img)
            self.update_profiles()
            self.fig.canvas.draw_idle()

    def toggle_autoscale(self, label):
        if label == "Auto Scale":
            self.auto_scale = not self.auto_scale
            self.update_profiles()
            self.fig.canvas.draw_idle()

    def update_cmap(self, label):
        self.cmap = label
        self.img.set_cmap(self.cmap)
        self.fig.canvas.draw_idle()

    def create_widgets(self):
        ax_x_slider = plt.axes([0.2, 0.05, 0.65, 0.03])
        self.x_slider = Slider(
            ax_x_slider, "X Slice", 0, self.nx - 1, valinit=self.cur_x, valstep=1
        )
        self.x_slider.on_changed(self.update_cross_section)

        ax_y_slider = plt.axes([0.2, 0.01, 0.65, 0.03])
        self.y_slider = Slider(
            ax_y_slider, "Y Slice", 0, self.ny - 1, valinit=self.cur_y, valstep=1
        )
        self.y_slider.on_changed(self.update_cross_section)

        ax_check_buttons = plt.axes([0.3, 0.85, 0.2, 0.1])
        self.check_buttons = CheckButtons(
            ax_check_buttons,
            ["Log Scale", "Auto Scale"],
            [self.log_scale, self.auto_scale],
        )
        self.check_buttons.on_clicked(self.toggle_logscale)
        self.check_buttons.on_clicked(self.toggle_autoscale)

        ax_cmap_radio = plt.axes([0.75, 0.85, 0.15, 0.15])
        self.cmap_radio = RadioButtons(
            ax_cmap_radio, ["viridis", "plasma", "gray", "magma", "hot"], active=4
        )
        self.cmap_radio.on_clicked(self.update_cmap)

    def on_click(self, event):
        if (
            event.inaxes == self.main_ax
            and event.xdata is not None
            and event.ydata is not None
        ):
            self.x_slider.set_val(int(event.xdata))
            self.y_slider.set_val(int(event.ydata))


class ImageXYProjectionViewer:
    def __init__(self, image_data):
        self.image_data = image_data
        self.ny, self.nx = image_data.shape
        self.z_max = image_data.max()
        self.cmap = "hot"
        self.log_scale = False

        # Compute projections
        self.x_projection = np.sum(image_data, axis=0)  # Sum along Y
        self.y_projection = np.sum(image_data, axis=1)  # Sum along X

        # Create figure
        self.fig, self.main_ax = plt.subplots(figsize=(7, 7))
        self.fig.subplots_adjust(top=0.85, bottom=0.2)

        divider = make_axes_locatable(self.main_ax)
        self.top_ax = divider.append_axes("top", 1.05, pad=0.1, sharex=self.main_ax)
        self.right_ax = divider.append_axes("right", 1.05, pad=0.1, sharey=self.main_ax)

        self.top_ax.xaxis.set_tick_params(labelbottom=False)
        self.right_ax.yaxis.set_tick_params(labelleft=False)

        self.update_norm()

        self.img = self.main_ax.imshow(
            self.image_data, origin="lower", cmap=self.cmap, norm=self.norm
        )

        # Add colorbar
        self.colorbar = self.fig.colorbar(
            self.img, ax=self.main_ax, orientation="vertical", shrink=0.8
        )

        self.main_ax.autoscale(enable=True)
        self.right_ax.autoscale(enable=True)
        self.top_ax.autoscale(enable=True)

        # Projection plots
        (self.v_proj,) = self.right_ax.plot(
            self.y_projection, np.arange(self.ny), "b-", label="Y Projection"
        )
        (self.h_proj,) = self.top_ax.plot(
            np.arange(self.nx), self.x_projection, "b-", label="X Projection"
        )

        self.create_widgets()

    def update_norm(self):
        """Update normalization mode based on log scale checkbox"""
        if self.log_scale:
            positive_values = self.image_data[self.image_data > 0]
            vmin = (
                max(positive_values.min(), 1e-3) if positive_values.size > 0 else 1e-3
            )
            self.norm = LogNorm(vmin=vmin, vmax=self.z_max)
        else:
            self.norm = None

    def update_colormap(self, label):
        """Update colormap dynamically from dropdown menu"""
        self.cmap = label
        self.img.set_cmap(self.cmap)
        self.colorbar.update_normal(self.img)
        self.fig.canvas.draw_idle()

    def toggle_logscale(self, label):
        """Toggle log scale for the image and redraw"""
        if label == "Log Scale":
            self.log_scale = not self.log_scale
            self.update_norm()
            self.img.set_norm(self.norm)
            self.colorbar.update_normal(self.img)
            self.log_button.label.set_text(
                "Log Scale: ON" if self.log_scale else "Log Scale: OFF"
            )
            self.fig.canvas.draw_idle()

    def create_widgets(self):
        """Create widgets"""

        ax_check_buttons = plt.axes([0.3, 0.85, 0.2, 0.1])
        self.check_buttons = CheckButtons(
            ax_check_buttons, ["Log Scale"], [self.log_scale]
        )
        self.check_buttons.on_clicked(self.toggle_logscale)

        ax_cmap_dropdown = plt.axes([0.7, 0.82, 0.2, 0.1])
        self.cmap_dropdown = RadioButtons(
            ax_cmap_dropdown, ["viridis", "plasma", "gray", "magma", "hot"], active=4
        )
        self.cmap_dropdown.on_clicked(self.update_colormap)

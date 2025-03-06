import numpy as np
from typing import TypedDict
import ipywidgets as widgets
from IPython.display import display, HTML
from matplotlib.colors import LogNorm, Normalize
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.figure import Figure
from matplotlib.widgets import Slider, RadioButtons, CheckButtons
from mpl_toolkits.axes_grid1 import make_axes_locatable
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
    def view(
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

    def __call__(self, *args, **kwargs):
        return self.view(*args, **kwargs)


class ImageInteractiveViewer:
    """
    An extension of ImageViewer that supports interactivity in Jupyter Notebook.
    """

    FIGURE_OPTIONS: dict[str, FigureOption] = {
        "Small (500x400)": {"figsize": (5, 4), "labelsize": 10},
        "Medium (700x500)": {"figsize": (7, 5), "labelsize": 12},
        "Large (1000x800)": {"figsize": (10, 8), "labelsize": 14},
    }

    def __init__(
        self,
        data: ImageDataType,
        title: str,
        colorbar: bool,
        cmap: str,
        log_scale: bool,
        xlabel: str,
        ylabel: str,
    ):
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
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

        figure_size_widget = widgets.Dropdown(
            options=list(self.FIGURE_OPTIONS.keys()),
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
            self._update_plot,
            data=widgets.fixed(data),
            colorbar=colorbar_widget,
            log_scale=log_scale_widget,
            cmap=cmap_widget,
            vmin=vmin_widget,
            vmax=vmax_widget,
            figure_size=figure_size_widget,
        )

        # Display the interactive plot
        display(interactive_plot)

    @classmethod
    def view(
        cls,
        data: ImageDataType,
        title: str = "",
        colorbar: bool = False,
        cmap: str = "viridis",
        log_scale: bool = False,
        xlabel: str = "",
        ylabel: str = "",
    ):
        """Create an interactive image viewer with ipywidgets."""

        return cls(data, title, colorbar, cmap, log_scale, xlabel, ylabel)

    def _update_plot(
        self,
        data: ImageDataType,
        colorbar: bool,
        log_scale: bool,
        cmap: str,
        vmin: float,
        vmax: float,
        figure_size: str,
    ):
        """Update plot based on widget values."""
        fig_options = self.FIGURE_OPTIONS[figure_size]
        figsize = fig_options["figsize"]
        labelsize = fig_options["labelsize"]

        plt.figure(figsize=figsize)
        norm = LogNorm(vmin=vmin, vmax=vmax) if log_scale else None
        plt.imshow(data.data, cmap=cmap, norm=norm)
        plt.title(self.title, fontsize=labelsize + 2)
        plt.xlabel(self.xlabel, fontsize=labelsize)
        plt.ylabel(self.ylabel, fontsize=labelsize)
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
    def view(
        cls,
        image_stack: ImageStackDataType,
        title: str = "",
        colorbar: bool = False,
        cmap: str = "hot",
        log_scale: bool = False,
        xlabel: str = "",
        ylabel: str = "",
        frame_duration: int = 200,
    ):
        """
        Creates and displays an animation using matplotlib.animation.

        Parameters:
            image_stack (ImageStackDataType): Stack of images to animate.
        """
        fig, ax = plt.subplots()

        # Compute global min/max values for consistent color scaling
        all_data = np.array([img.data for img in image_stack.data])
        vmin, vmax = all_data.min(), all_data.max()

        # Define log normalization if log scale is enabled
        norm = LogNorm(vmin=max(1e-34, vmin), vmax=vmax) if log_scale else None

        # Add colorbar if requested
        if colorbar:
            cbar = fig.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax)

        frames = []

        for img in image_stack.data:
            img_array = np.array(img.data)
            img_normalized = (
                (img_array - img_array.min())
                * 255
                / (img_array.max() - img_array.min())
            ).astype(np.uint8)
            ax.title.set_text(title)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            frame = ax.imshow(img_normalized, cmap=cmap, animated=True, norm=norm)
            frames.append([frame])

        ani = animation.ArtistAnimation(fig, frames, interval=frame_duration, blit=True)

        # Display the animation
        display(HTML(ani.to_jshtml()))
        plt.close()


class ImageCrossSectionInteractiveViewer:
    """
    An interactive viewer for 2D images with cross-sections.
    The viewer displays an image with vertical and horizontal cross-sections.
    The user can interact with the image by moving the cross-sections, changing the colormap,
    toggling log scale, and auto-scaling the profiles.

    Note: This viewer is designed for Jupyter Notebook. In order to be correctly displayed,
    please add on the first cell of the notebook the following line:
    %matplotlib ipympl. This will enable the interactive mode for matplotlib.
    Also take into account that the interactive mode may interferes with
    other viewers in the notebook.

    Example of usage:
        viewer = ImageCrossSectionInteractiveViewer.view(image_data)
    """

    def __init__(
        self,
        image_data: ImageDataType,
        title: str = "",
        colorbar: bool = False,
        cmap: str = "hot",
        log_scale: bool = False,
        xlabel: str = "",
        ylabel: str = "",
    ):
        self._image_data = image_data.data
        self._ny, self._nx = self._image_data.shape
        self._cur_x = self._nx // 2
        self._cur_y = self._ny // 2
        self._z_max = self._image_data.max()
        self._z_min = self._image_data.min()
        self._cmap = cmap
        self._log_scale = log_scale
        self._auto_scale = False
        self._title = title
        self._use_colorbar = colorbar
        self._xlabel = xlabel
        self._ylabel = ylabel

        self._fig, self._main_ax = plt.subplots(figsize=(7, 7))
        self._fig.subplots_adjust(top=0.85, bottom=0.2)

        divider = make_axes_locatable(self._main_ax)
        self._top_ax = divider.append_axes("top", 1.05, pad=0.1, sharex=self._main_ax)
        self._right_ax = divider.append_axes(
            "right", 1.05, pad=0.1, sharey=self._main_ax
        )

        self._top_ax.xaxis.set_tick_params(labelbottom=False)
        self._right_ax.yaxis.set_tick_params(labelleft=False)

        self._update_norm()

        self._img = self._main_ax.imshow(
            self._image_data, origin="lower", cmap=self._cmap, norm=self._norm
        )
        if self._use_colorbar:
            self._colorbar = self._fig.colorbar(
                self._img, ax=self._main_ax, orientation="vertical", shrink=0.8
            )

        self._top_ax.set_title(title)
        self._main_ax.set_xlabel(xlabel)
        self._main_ax.set_ylabel(ylabel)

        self._main_ax.autoscale(enable=False)
        self._right_ax.autoscale(enable=False)
        self._top_ax.autoscale(enable=False)

        (self._v_line,) = self._main_ax.plot(
            [self._cur_x, self._cur_x], [0, self._ny], "r-"
        )
        (self._h_line,) = self._main_ax.plot(
            [0, self._nx], [self._cur_y, self._cur_y], "g-"
        )

        (self._v_prof,) = self._right_ax.plot(
            self._image_data[:, self._cur_x], np.arange(self._ny), "r-"
        )
        (self._h_prof,) = self._top_ax.plot(
            np.arange(self._nx), self._image_data[self._cur_y, :], "g-"
        )

        self._fig.canvas.mpl_connect("button_press_event", self._on_click)
        self._create_widgets()
        self._update_profiles()

    @classmethod
    def view(
        cls,
        image_data: ImageDataType,
        title: str = "",
        colorbar: bool = False,
        cmap: str = "hot",
        log_scale: bool = False,
        xlabel: str = "",
        ylabel: str = "",
    ):
        return cls(image_data, title, colorbar, cmap, log_scale, xlabel, ylabel)

    def _update_norm(self):
        """Update normalization mode based on log scale checkbox"""
        if self._log_scale:
            positive_values = self._image_data[self._image_data > 0]
            vmin = (
                max(positive_values.min(), 1e-3) if positive_values.size > 0 else 1e-3
            )
            self._norm = LogNorm(vmin=vmin, vmax=self._z_max)
        else:
            self._norm = None

    def _update_cross_section(self, val=None):
        """Update cross-sections based on slider values"""
        self._cur_x = int(self._x_slider.val)
        self._cur_y = int(self._y_slider.val)
        self._cur_x = np.clip(self._cur_x, 0, self._nx - 1)
        self._cur_y = np.clip(self._cur_y, 0, self._ny - 1)

        self._v_line.set_data([self._cur_x, self._cur_x], [0, self._ny])
        self._h_line.set_data([0, self._nx], [self._cur_y, self._cur_y])

        self._update_profiles()
        self._img.set_data(self._image_data)
        self._fig.canvas.draw_idle()

    def _update_profiles(self):
        """Update vertical and horizontal profiles based on current cross-sections"""
        v_prof_data = self._image_data[:, self._cur_x]
        h_prof_data = self._image_data[self._cur_y, :]

        margin = 0.05  # 5% margin for better visualization

        if self._auto_scale:
            v_min, v_max = v_prof_data.min(), v_prof_data.max()
            h_min, h_max = h_prof_data.min(), h_prof_data.max()
        else:
            v_min, v_max = self._z_min, self._z_max
            h_min, h_max = self._z_min, self._z_max
        v_range = v_max - v_min
        h_range = h_max - h_min

        v_min -= v_range * margin
        v_max += v_range * margin
        h_min -= h_range * margin
        h_max += h_range * margin

        # Ensure positive limits for log scale
        if self._log_scale:
            v_min = max(v_min, 1e-34)  # Avoid non-positive values
            h_min = max(h_min, 1e-34)

        # Update axes limits
        self._right_ax.set_xlim(v_min, v_max)
        self._v_prof.set_data(np.arange(self._ny), v_prof_data)
        self._top_ax.set_ylim(h_min, h_max)
        self._h_prof.set_data(np.arange(self._nx), h_prof_data)

        self._v_prof.set_data(v_prof_data, np.arange(self._ny))
        self._h_prof.set_data(np.arange(self._nx), h_prof_data)

        self._fig.canvas.draw_idle()

    def _toggle_logscale(self, label):
        """Toggle log scale for the image and redraw"""
        if label == "Log Scale":
            self._log_scale = not self._log_scale
            self._update_norm()
            self._img.set_norm(self._norm)
            if self._use_colorbar:
                self._colorbar.update_normal(self._img)
            self._update_profiles()
            self._fig.canvas.draw_idle()

    def _toggle_autoscale(self, label):
        """Toggle auto scale for the profiles and redraw"""
        if label == "Auto Scale":
            self._auto_scale = not self._auto_scale
            self._update_profiles()
            self._fig.canvas.draw_idle()

    def _update_cmap(self, label):
        """Update colormap dynamically from dropdown menu"""
        self._cmap = label
        self._img.set_cmap(self._cmap)
        self._fig.canvas.draw_idle()

    def _create_widgets(self):
        """Create widgets for the interactive viewer"""
        ax_x_slider = plt.axes([0.2, 0.05, 0.65, 0.03])
        self._x_slider = Slider(
            ax_x_slider, "X Slice", 0, self._nx - 1, valinit=self._cur_x, valstep=1
        )
        self._x_slider.on_changed(self._update_cross_section)

        ax_y_slider = plt.axes([0.2, 0.01, 0.65, 0.03])
        self._y_slider = Slider(
            ax_y_slider, "Y Slice", 0, self._ny - 1, valinit=self._cur_y, valstep=1
        )
        self._y_slider.on_changed(self._update_cross_section)

        ax_check_buttons = plt.axes([0.5, 0.9, 0.2, 0.1])
        self._check_buttons = CheckButtons(
            ax_check_buttons,
            ["Log Scale", "Auto Scale"],
            [self._log_scale, self._auto_scale],
        )
        self._check_buttons.on_clicked(self._toggle_logscale)
        self._check_buttons.on_clicked(self._toggle_autoscale)

        ax_cmap_radio = plt.axes([0.75, 0.85, 0.15, 0.15])
        options_list = ["viridis", "plasma", "gray", "magma", "hot"]
        for i, option in enumerate(options_list):
            if option == self._cmap:
                active = i
                break
        self._cmap_radio = RadioButtons(
            ax_cmap_radio, ["viridis", "plasma", "gray", "magma", "hot"], active=i
        )
        self._cmap_radio.on_clicked(self._update_cmap)

    def _on_click(self, event):
        """Update cross-sections based on mouse click"""
        if (
            event.inaxes == self._main_ax
            and event.xdata is not None
            and event.ydata is not None
        ):
            self._x_slider.set_val(int(event.xdata))
            self._y_slider.set_val(int(event.ydata))


class ImageXYProjectionViewer:
    """
    An Viewer for 2D images with X and Y projections.
    The viewer displays an image with vertical and horizontal projections.
    The user can set the colormap and set the log scale for the image.

    Note: This viewer is designed for Jupyter Notebook.

    Example of usage:
        viewer = ImageXYProjectionViewer.view(image_data)
    """

    @classmethod
    def view(
        cls,
        image: ImageDataType,
        title: str = "",
        colorbar: bool = False,
        cmap: str = "hot",
        log_scale: bool = False,
        xlabel: str = "",
        ylabel: str = "",
    ):
        """Display an image with X and Y projections."""
        image_data = image.data
        ny, nx = image_data.shape
        z_max = image_data.max()

        # Compute projections
        x_projection = np.sum(image_data, axis=0)  # Sum along Y
        y_projection = np.sum(image_data, axis=1)  # Sum along X

        # Create figure
        fig, main_ax = plt.subplots(figsize=(7, 7))
        fig.subplots_adjust(top=0.85, bottom=0.2)

        divider = make_axes_locatable(main_ax)
        top_ax = divider.append_axes("top", 1.05, pad=0.1, sharex=main_ax)
        right_ax = divider.append_axes("right", 1.05, pad=0.1, sharey=main_ax)
        top_ax.set_title(title)
        main_ax.set_xlabel(xlabel)
        main_ax.set_ylabel(ylabel)

        top_ax.xaxis.set_tick_params(labelbottom=False)
        right_ax.yaxis.set_tick_params(labelleft=False)

        norm = LogNorm(vmin=1e-2, vmax=z_max) if log_scale else None

        img = main_ax.imshow(image_data, origin="lower", cmap=cmap, norm=norm)

        # Add colorbar
        if colorbar:
            color_bar = fig.colorbar(
                img, ax=main_ax, orientation="vertical", shrink=0.8
            )

        main_ax.autoscale(enable=True)
        right_ax.autoscale(enable=True)
        top_ax.autoscale(enable=True)

        # Projection plots
        (v_proj,) = right_ax.plot(
            y_projection, np.arange(ny), "b-", label="Y Projection"
        )
        (h_proj,) = top_ax.plot(np.arange(nx), x_projection, "b-", label="X Projection")

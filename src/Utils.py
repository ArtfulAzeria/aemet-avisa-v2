class Utils:
    def __init__(self):
        self.test = "test"

    @staticmethod
    def clean_axes(ax, remove_ticks=True):
        ax.spines['bottom'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.patch.set_visible(False)

        if remove_ticks:
            ax.xaxis.set_ticks([])
            ax.yaxis.set_ticks([])


    @staticmethod
    def clean_figure(fig):
        fig.patch.set_visible(False)

    @staticmethod
    def clean_img(ax, fig):
        Utils.clean_axes(ax)
        Utils.clean_figure(fig)

    @staticmethod
    def normalize_rgb(rgb):
        return tuple(int(c * 255) for c in rgb)

    @staticmethod
    def rgba_to_bgr(rgba):
        return Utils.normalize_rgb(rgba[:3][::-1])
from cytokit.ops.op import CytokitOp
import logging

logger = logging.getLogger(__name__)

# Note on cropping -- example settings for real data (akoya tonsil):
# - acquisition image (1920 x 1440) (cols x rows)  (images are wider than they are tall)
# - tile dims (1344 x 1008) (cols x rows)
# - tile overlap x = 576, tile overlap y = 432 (x refers to columns and y refers to rows)


def get_slice(config):
    """Get 2D slice defining crop operation appropriate for given configuration"""
    nw, nh = config.raw_tile_width, config.raw_tile_height
    ow, oh = config.overlap_x, config.overlap_y
    w_start, h_start = ow // 2, oh // 2
    w_stop, h_stop = w_start + nw, h_start + nh
    return [slice(h_start, h_stop), slice(w_start, w_stop)]


def apply_slice(img, crop_slice):
    """Apply cropping slice to trailing image dimensions"""
    if img.ndim < 2:
        raise ValueError('Expecting at least 2 dimensions in image (shape of given array = {})'.format(img.shape))
    slices = tuple([slice(None, None) for _ in range(img.ndim - 2)] + crop_slice)
    return img[slices]


class CytokitTileCrop(CytokitOp):

    def __init__(self, config):
        super().__init__(config)

    def _run(self, tile, **kwargs):

        # Check to see if zero overlap configured and return immediately if so
        if not self.config.overlap_x and not self.config.overlap_y:
            return tile

        # Check to see if tile dimensions indicate that cropping is not possible and return immediately if so
        ih, iw = tile.shape[-2:]
        nw, nh = self.config.raw_tile_width, self.config.raw_tile_height
        if iw <= nw or ih <= nh:
            logger.warning(
                'Tile cropping is attempting to run on a tile of shape {} but the configured '
                'target height and width {} already exceeds or equals the size of the provided tile '
                'in the image dimensions.  The tile will be returned as-is but this could indicate '
                'an issue and if not, tile crop should be disabled'
                .format(tile.shape, (nh, nw))
            )
            return tile

        # Otherwise, run the cropping operation
        slice_arr = get_slice(self.config)
        self.record({'slice': [str(v) for v in slice_arr]})
        return apply_slice(tile, slice_arr)

#! /usr/bin/env python3
# 
# Now let's assume there are N solid black rectangles in the image. Find them
# all and return their coordinates. For example:
# image = [
#	[1, 1, 1, 1, 1, 1, 1],
#	[1, 1, 1, 1, 1, 1, 1],
#	[1, 1, 1, 0, 0, 0, 1],
#	[1, 0, 1, 0, 0, 0, 1],
#	[1, 0, 1, 1, 1, 1, 1],
#	[1, 0, 1, 0, 0, 1, 1],
#	[1, 1, 1, 0, 0, 1, 1],
#	[1, 1, 1, 1, 1, 1, 1],
# ];



# This program creates a dictionary of rectangles.  The key is the upper left
# corner, stored as a tuple.  The value is the width and height of the rectangle
# The advantage of using a dictionary over a list is that the dictionary is
# independent of the algorithm used to find the rectangles, for example, searching
# from top to bottom instead of bottom to top.

import pprint


pp = pprint.PrettyPrinter(indent=4)


def find_rectangles ( image ) :
    """Returns a dictionary keyed by row, col of the upper left corner and
the values are the width and height"""
    rows = len(image)   # assuming that image is really a rectangle
    cols = len(image[0])   # Again, assuming the image is really a rectangle
    d = {}
    for row in range(rows) :
        for col in range(cols) :
            if image[row][col] == 0 :
# we found the upper left corner, now search the extent of the rectangle
                top = row
                left = col
# Now that we've found the upper left corner, search for the right edge
# and the bottom
                for row_i in range(row, rows) :
                    for col_i in range ( col, cols ):
                        if image[row_i][col_i] == 0 :
# Mark that we've already found this pixel in a rectangle.  There might be a
# more efficient way to do this, think about it if there is time.
                            image[row_i][col_i] == 2
                        if image[row_i][col_i] == 1 or col_i == cols-1 :
                            width = col_i - left
                            break   # we're done searching for the right edge
# searching for the bottom
                    if image[row_i][left] == 1 or row_i == rows - 1 :
                        height = row_i - top
                d[(top,left)] = ( width, height )
# if we're here, then it's time to search the next pixel.  When the loop is
# done, we can return the dictionary.
    return d



if __name__ == "__main__" :

    def test ( d, rectangles ):
        """Throw an assert exception if the results of the find_rectangles
subroutine does not equal dictionary d"""
        if ( len( set(d.items()) ^ set(rectangles.items()) ) ) == 0 :
            print ( "The result is correct" )
        else :
# This could be made more intelligent - do so if I have time
            print ( "The nominal value is: " )
            pp.pprint ( rectangles )
            print ( "The returned value, which is wrong, is: " )
            pp.pprint ( d )
# Do I raise an AssertionError?  That would catch my attention
            raise AssertionError

# This is the image in the problem statement
    image = [
	[1, 1, 1, 1, 1, 1, 1],
	[1, 1, 1, 1, 1, 1, 1],
	[1, 1, 1, 0, 0, 0, 1],
	[1, 0, 1, 0, 0, 0, 1],
	[1, 0, 1, 1, 1, 1, 1],
	[1, 0, 1, 0, 0, 1, 1],
	[1, 1, 1, 0, 0, 1, 1],
	[1, 1, 1, 1, 1, 1, 1],
 ];
    rectangles = {(2,3): (3,2), (3,1): (1,3), (5, 3): (2,2) }
    d = find_rectangles( image )
    pp.pprint ( d )
    test ( d, rectangles )

# This is the image with a rectangle at the right edge
    image = [
	[1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1],
	[1, 1, 1, 0, 0, 0, 0],
	[1, 0, 1, 0, 0, 0, 0],
	[1, 0, 1, 1, 1, 1, 1],
	[1, 0, 1, 0, 0, 1, 1],
	[1, 1, 1, 0, 0, 1, 1],
	[1, 1, 1, 1, 1, 1, 1],
 ];
    rectangles = {(2,3): (4,2), (3,1): (1,3), (5, 3): (2,2) }
    d = find_rectangles( image )
    pp.pprint ( d )
    test ( d, rectangles )

# This is the image with a rectangle at the bottom
    image = [
	[1, 1, 1, 1, 1, 1, 1],
	[1, 1, 1, 1, 1, 1, 1],
	[1, 1, 1, 0, 0, 0, 1],
	[1, 0, 1, 0, 0, 0, 1],
	[1, 0, 1, 1, 1, 1, 1],
	[1, 0, 1, 0, 0, 1, 1],
	[1, 1, 1, 0, 0, 1, 1],
	[1, 1, 1, 0, 0, 1, 1],
 ];
    rectangles = {(2,3): (3,2), (3,1): (1,3), (5, 3): (2,3) }
    d = find_rectangles( image )
    pp.pprint ( d )
    test ( d, rectangles )

    


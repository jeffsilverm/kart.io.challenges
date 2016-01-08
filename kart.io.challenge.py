#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# Imagine we have an image where every pixel is white or black. We’ll represent
# this image as a simple 2D array (0 = black, 1 = white). The image you get is 
# known to have a single black rectangle on a white background. Find this rectangle 
# and return its coordinates. Here’s a sample “image” using JavaScript (feel free
# to rewrite in your language of choice):

import numpy as np


def find_rectangle ( image ):
  (rows, cols) = image.shape
  
  print ("The size of the array is (%d, %d)" % (rows, cols) )

  right = None
  left = None
  top = None
  bottom = None
# Search for the upper left corner
  for row in range(rows) :
    for col in range(cols) :
      if image[row][col] == 0 and top == None:
# The first thing we're going to come to the upper left corner, so save it
        ( top, left ) = (row, col)
        for col in range(col,cols) :
# We're now looping through the black rectangle: the upper right edge is when
# the image turns white
          if image[row][col] == 1 :
            right = col-1
          elif col == cols-1 :   # we're at the right edge
            right = col
          if right != None :
            break
        for row in range(row, rows) :
          if image[row][left] == 1 :
            bottom = row-1
          elif  row == rows-1 :
            bottom = row
          if bottom != None :
            break
        break  # We don't have to search for the upper left corner
  return ( top, left, bottom, right )
        










if __name__ == "__main__" :
  

  def test ( image, top, left, bottom, right ) :
    """This subroutine tests the image against the 4 nominal values, and throws
assertion errors if the nominal val
ue is wrong"""


    (t,l,b,r) = find_rectangle( image )
    assert t == top, "Upper row is %d, should be %d" % (t, top)
    assert l == left, "left colum is %d, should be %d" % (l, left)
    assert b == bottom, "Lower row is %d, should be %d" % (b, bottom )
    assert r == right, "right column is %d, should be %d" % (r, right)
# Computers start counting at 0, but humans start counting at 1
    print("The black rectangle is at (%d,%d) to (%d,%d)" % ( t+1, l+1, b+1, r+1 ))


# This is the image given in the problem statement
  image = np.array ([
	[1, 1, 1, 1, 1, 1, 1],
	[1, 1, 1, 1, 1, 1, 1],
	[1, 1, 1, 0, 0, 0, 1],
	[1, 1, 1, 0, 0, 0, 1],
	[1, 1, 1, 1, 1, 1, 1],
])
  
  print ("Given image from the problem statement")
  test ( image, 2, 3, 3, 5 )

# Another test case: rectangle at the right edge
  image = np.array ([
	[1, 1, 1, 1, 1, 1, 1],
	[1, 1, 1, 1, 1, 1, 1],
	[1, 1, 1, 0, 0, 0, 0],
	[1, 1, 1, 0, 0, 0, 0],
	[1, 1, 1, 1, 1, 1, 1],
])
  print ("Rectangle at the right edge")
  test ( image, 2, 3, 3, 6 )
 
# Another test case: rectangle at the left edge
  image = np.array ([
	[1, 1, 1, 1, 1, 1, 1],
	[1, 1, 1, 1, 1, 1, 1],
	[0, 0, 0, 0, 0, 0, 1],
	[0, 0, 0, 0, 0, 0, 1],
	[1, 1, 1, 1, 1, 1, 1],
])
  print ("Rectangle at the left edge")
  test ( image, 2, 0, 3, 5)

# Another test case: rectangle at the bottom edge
  image = np.array ([
	[1, 1, 1, 1, 1, 1, 1],
	[1, 1, 1, 1, 1, 1, 1],
	[1, 0, 0, 0, 0, 0, 1],
	[1, 0, 0, 0, 0, 0, 1],
	[1, 0, 0, 0, 0, 0, 1],
])
  print ("Rectangle at the bottom")
  test ( image, 2, 1, 4, 5)

  


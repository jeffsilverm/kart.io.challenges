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

  ul = 0
  for row in range(rows) :
    for col in range(cols) :
      if image[row][col] == 0 and ul == 0 :
# The first thing we're going to come to the upper left corner, so save it
        ul = (row, col)
        for col_i in range(col,cols) :
# We're now looping through the black rectangle: the upper right edge is when
# the image turns white
          if image[row][col_i] == 1 :
            ur = (row, col_i) 
            break
# I can simplify this but I am in a hurry
      elif image[row][col] == 0 and ul != 0 :
        ll = (row, col)
        break
# go to the next row


  return (( ul[0],ul[1],ll[0],ur[1]) )




if __name__ == "__main__" :
  

  image = np.array ([
	[1, 1, 1, 1, 1, 1, 1],
	[1, 1, 1, 1, 1, 1, 1],
	[1, 1, 1, 0, 0, 0, 1],
	[1, 1, 1, 0, 0, 0, 1],
	[1, 1, 1, 1, 1, 1, 1],
])
  (ur,lc,lr,rc) = find_rectangle( image )
  assert ul == 3, "Upper left corner is %d, should be 3" % ul
  assert ur == 5, "Upper right corner is %d, should be 5" % ur
  assert ll == 3, "Lower left corner is %d, should be 3" % ll
  assert lr == 7, "lower right corner is %d, should be 7" % lr
# Computers start counting at 0, but humans start counting at 1
  print("The black rectangle is at (%d,%d) to (%d,%d)" % ( ur+1, lc+1, lr+1, rc+1 ))





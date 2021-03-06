# Copyright (c) 2016 Jamie Bull
# =======================================================================
#  Distributed under the MIT License.
#  (See accompanying file LICENSE or copy at
#  http://opensource.org/licenses/MIT)
# =======================================================================
"""
Build IDF geometry from minimal inputs.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from geomeppy.polygons import Polygon3D
from geomeppy.vectors import Vector3D


class Zone(object):
    
    def __init__(self, name, surfaces):
        self.name = name
        self.walls = [s for s in surfaces['walls'] if s.area > 0]
        self.floors = surfaces['floors']
        self.roofs = surfaces['roofs']
        self.ceilings = surfaces['ceilings']
        

class Block(object):
    
    def __init__(self, name, coordinates, height, num_stories=1,
                 below_ground_stories=0, below_ground_storey_height=2.5):
        """Represents a single block for translation into an IDF.
        
        Parameters
        ----------
        name : str
            A name for the block.
        coordinates : list
            A list of (x, y) tuples representing the building outline.
        height : float
            The height of the block roof above ground level.
        num_stories : int, optional
            The total number of stories including basement stories. Default : 1.
        below_ground_stories : int, optional
            The number of stories below ground. Default : 0.
        below_ground_storey_height : float, optional
            The height of each basement storey. Default : 2.5.
        """
        self.name = name
        if coordinates[0] == coordinates[-1]:
            coordinates.pop()
        self.coordinates = coordinates
        self.height = height
        self.num_stories = num_stories
        self.num_below_ground_stories = below_ground_stories
        self.below_ground_storey_height = below_ground_storey_height
    
    @property
    def stories(self):
        """A list of dicts of the surfaces of each storey in the block.
        
        Returns
        -------
        list of dicts
            Dicts have the format:
                {'floors': [...], 'ceilings': [...],
                'walls': [...], 'roofs': [...]}
        
        """
        stories = []
        if self.num_below_ground_stories != 0:
            floor_no = -self.num_below_ground_stories
        else:
            floor_no = 0
        for f, c, w, r in zip(
                self.floors, self.ceilings, self.walls, self.roofs):
            stories.append({
                'storey_no': floor_no,
                'floors': f, 'ceilings': c, 'walls': w, 'roofs': r})
            floor_no += 1
        return stories
    
    @property
    def footprint(self):
        """Ground level outline of the block.
        
        Returns
        -------
        Polygon3D
        
        """
        coordinates = [(v[0], v[1], 0) for v in self.coordinates]
        return Polygon3D(coordinates)
    
    @property
    def storey_height(self):
        """Height of above ground stories.
        
        Returns
        -------
        float
        
        """
        return self.height / (self.num_stories - self.num_below_ground_stories)
    
    @property
    def floor_heights(self):
        """Floor height for each storey in the block.
        
        Returns
        -------
        list
        
        """
        lfl = self.lowest_floor_level
        sh = self.storey_height
        floor_heights = [lfl + sh * i for i in range(self.num_stories)]
        return floor_heights

    @property
    def ceiling_heights(self):
        """Ceiling height for each storey in the block.
        
        Returns
        -------
        list
        
        """
        lfl = self.lowest_floor_level
        sh = self.storey_height
        ceiling_heights = [lfl + sh * (i+1) for i in range(self.num_stories)]
        return ceiling_heights

    @property
    def lowest_floor_level(self):
        """Floor level of the lowest basement storey.
        
        Returns
        -------
        float
        
        """
        return -(self.num_below_ground_stories * 
                 self.below_ground_storey_height)
    
    @property
    def walls(self):
        """Coordinates for each wall in the block.
        
        These are ordered as a list of lists, one for each storey.
        
        Returns
        -------
        list
        
        """
        walls = []
        for fh, ch in zip(self.floor_heights, self.ceiling_heights):
            
            floor_walls = [make_wall(edge, fh, ch)
                           for edge in self.footprint.edges]
            walls.append(floor_walls)
        return walls
    
    @property
    def floors(self):
        """Coordinates for each floor in the block.
        
        Returns
        -------
        list
        
        """
        floors = [[self.footprint.invert_orientation() + Vector3D(0,0,fh)]
                  for fh in self.floor_heights]
        return floors

    @property
    def ceilings(self):
        """Coordinates for each ceiling in the block.
        
        Returns
        -------
        list
        
        """
        ceilings = [[self.footprint + Vector3D(0,0,ch)]
                    for ch in self.ceiling_heights[:-1]]
        
        ceilings.append('')
        return ceilings
    
    @property
    def roofs(self):
        """Coordinates for each roof of the block.
        
        This returns a list with an entry for each floor for consistency with
        the other properties of the Block object, but should only have roof
        coordinates in the list in the final position.
        
        Returns
        -------
        list
        
        """
        roofs = [[None] for ch in self.ceiling_heights[:-1]]
        roofs.append([self.footprint + Vector3D(0,0,self.height)])
        return roofs

    @property
    def surfaces(self):
        """Coordinates for all the surfaces in the block.
        
        Returns
        -------
        dict
        
        """
        return {'walls': self.walls, 
                'ceilings': self.ceilings,
                'roofs': self.roofs,
                'floors': self.floors}

def make_wall(edge, fh, ch):
    return Polygon3D([edge.p1 + (0,0,ch),  # upper left
                      edge.p1 + (0,0,fh),  # lower left
                      edge.p2 + (0,0,fh),  # lower right
                      edge.p2 + (0,0,ch),  # upper right
                      ])
"""
Mimic a few items from scipy since it is a HUGE memory hog and
will cause 32 bit applications to crash.
"""
import numpy as np
import math
# import scipy

class QRotation:
    """
    Rotation class.  
    """
    def __init__ (self):
        self.M = np.array([[1.0,0.0,0.0], [0.0,1.0,0.0], [0.0,0.0,1.0]])
    def __str__(self):
        return f"QRotation is \n{self.M}"
    def __mul__(S, O):
        R = QRotation()
        R.M[0][0] = S.M[0][0]*O.M[0][0] + S.M[0][1]*O.M[1][0] + S.M[0][2]*O.M[2][0]
        R.M[0][1] = S.M[0][0]*O.M[0][1] + S.M[0][1]*O.M[1][1] + S.M[0][2]*O.M[2][1]
        R.M[0][2] = S.M[0][0]*O.M[0][2] + S.M[0][1]*O.M[1][2] + S.M[0][2]*O.M[2][2]
        R.M[1][0] = S.M[1][0]*O.M[0][0] + S.M[1][1]*O.M[1][0] + S.M[1][2]*O.M[2][0]
        R.M[1][1] = S.M[1][0]*O.M[0][1] + S.M[1][1]*O.M[1][1] + S.M[1][2]*O.M[2][1]
        R.M[1][2] = S.M[1][0]*O.M[0][2] + S.M[1][1]*O.M[1][2] + S.M[1][2]*O.M[2][2]
        R.M[2][0] = S.M[2][0]*O.M[0][0] + S.M[2][1]*O.M[1][0] + S.M[2][2]*O.M[2][0]
        R.M[2][1] = S.M[2][0]*O.M[0][1] + S.M[2][1]*O.M[1][1] + S.M[2][2]*O.M[2][1]
        R.M[2][2] = S.M[2][0]*O.M[0][2] + S.M[2][1]*O.M[1][2] + S.M[2][2]*O.M[2][2]
        return  R

    def from_matrix(self,mat):
        self.M = mat
        return self

    def from_axis_angle(self, axis, angle):
        """
        Angle in radians
        see p 466 of Graphics Gems 1
        """
        x = axis[0]
        y = axis[1]
        z = axis[2]
        s = math.sin(angle)
        c = math.cos(angle)
        t = 1.0 - c
        self.M[0][0] = t * x * x + c
        self.M[0][1] = t * x * y + s * z
        self.M[0][2] = t * x * z - s * y
        self.M[1][0] = t * x * y - s * z
        self.M[1][1] = t * y * y + c
        self.M[1][2] = t * y * z + s * x
        self.M[2][0] = t * x * z + s * y
        self.M[2][1] = t * y * z - s * x
        self.M[2][2] = t * z * z + c
        return self

    def inv(self):
        N = QRotation()
        N.M = np.linalg.inv(self.M)
        return N
    def as_euler_xyz(self):
        """ Return the euler angles in degrees.  No error checking."""
        b = math.asin(-self.M[0][2])
        Cb = math.cos(b)
        nz = math.isclose(Cb,0.0, abs_tol = 1e-09)
        nz12 = math.isclose(self.M[1][2],0.0, abs_tol = 1e-09)
        nz22 = math.isclose(self.M[2][2],0.0, abs_tol = 1e-09)
        if (Cb == 0.0) or (nz and nz12 and nz22):
            a = math.atan2(-self.M[1][0], self.M[1][1])
            c = 0.0
        else:
            a = math.atan2(self.M[1][2], self.M[2][2])
            c = math.atan2(self.M[0][1], self.M[0][0])

        return np.array([math.degrees(a), math.degrees(b), math.degrees(c)])

    def as_euler(self, order:str):
        if order == "xyz":
            return self.as_euler_xyz()
        print(f"Don't know that rotation order yet.")
        return np.array([0.0,0.0,0.0])



def run_tests():
    M = QRotation()
    print(f"M is {M}")
    # R = scipy.spatial.transform.Rotation.from_matrix([[1.0,0.0,0.0], [0.0,1.0,0.0], [0.0,0.0,1.0]])
    # print(f"R is {R.as_matrix()}")

#print(f"__name__ is {__name__}")
#print(f"__file__ is {__file__}")
if __name__ == "__main__":
    run_tests()

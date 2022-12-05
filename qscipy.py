"""
Mimic a few items from scipy since it is a HUGE memory hog and
will cause 32 bit applications to crash.
"""
import numpy as np
import math
import sys

class QRotation:
    """
    Rotation class.  Use numpy array type. Internally kept as a matrix.
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

    @staticmethod
    def from_matrix(mat):
        R = QRotation()
        R.M = mat
        return R

    @staticmethod
    def from_axis_angle(axis, angle):
        """
        Angle in radians
        see p 466 of Graphics Gems 1
        """
        R = QRotation()
        x = axis[0]
        y = axis[1]
        z = axis[2]
        s = math.sin(angle)
        c = math.cos(angle)
        t = 1.0 - c
        R.M[0][0] = t * x * x + c
        R.M[0][1] = t * x * y + s * z
        R.M[0][2] = t * x * z - s * y
        R.M[1][0] = t * x * y - s * z
        R.M[1][1] = t * y * y + c
        R.M[1][2] = t * y * z + s * x
        R.M[2][0] = t * x * z + s * y
        R.M[2][1] = t * y * z - s * x
        R.M[2][2] = t * z * z + c
        return R
    @staticmethod
    def from_x_rot(deg):
        R = QRotation()
        rad = math.radians(deg)
        s = math.sin(rad)
        c = math.cos(rad)
        R.M[0][0] = 1.0
        R.M[0][1] = 0.0
        R.M[0][2] = 0.0
        R.M[1][0] = 0.0
        R.M[1][1] = c
        R.M[1][2] = s
        R.M[2][0] = 0.0
        R.M[2][1] = -s
        R.M[2][2] = c
        return R
    @staticmethod
    def from_y_rot(deg):
        R = QRotation()
        rad = math.radians(deg)
        s = math.sin(rad)
        c = math.cos(rad)
        R.M[0][0] = c
        R.M[0][1] = 0.0
        R.M[0][2] = -s
        R.M[1][0] = 0.0
        R.M[1][1] = 1.0
        R.M[1][2] = 0.0
        R.M[2][0] = s
        R.M[2][1] = 0.0
        R.M[2][2] = c
        return R
    @staticmethod
    def from_z_rot(deg):
        R = QRotation()
        rad = math.radians(deg)
        s = math.sin(rad)
        c = math.cos(rad)
        R.M[0][0] = c
        R.M[0][1] = s
        R.M[0][2] = 0.0
        R.M[1][0] = -s
        R.M[1][1] = c
        R.M[1][2] = 0.0
        R.M[2][0] = 0.0
        R.M[2][1] = 0.0
        R.M[2][2] = 1.0
        return R
    @staticmethod
    def from_euler(order:str, e):
        R = QRotation()
        Rx = QRotation.from_x_rot(e[0])
        Ry = QRotation.from_y_rot(e[1])
        Rz = QRotation.from_z_rot(e[2])
        for axis in order:
            if axis == 'x' or axis == 'X':
                R = R * Rx
            elif axis == 'y' or axis == 'Y':
                R = R * Ry
            else:
                R = R * Rz
        return R

    @staticmethod
    def from_quat(q):
        R = QRotation()
        x = q[0]
        y = q[1]
        z = q[2]
        w = q[3]
        xx = x * x
        yy = y * y
        zz = z * z
        ww = w * w
        div = xx + yy + zz + ww
        if div > sys.float_info.epsilon:
            R.M[0][0] = (ww + xx - yy - zz) / div
            R.M[0][1] = (2.0 * (x * y + w * z)) / div
            R.M[0][2] = (2.0 * (x * z - w * y)) / div

            R.M[1][0] = (2.0 * (x * y - w * z)) / div
            R.M[1][1] = (ww - xx + yy - zz) / div
            R.M[1][2] = (2.0 *(y * z + w * x)) / div

            R.M[2][0] = (2.0 * (x * z + w * y)) / div
            R.M[2][1] = (2.0 * (y * z - w * x)) / div
            R.M[2][2] = (ww - xx - yy + zz) / div    
        return R                

    def inv(self):
        self.M = np.linalg.inv(self.M)
        return self
    def inv(self):
        return np.linalg.det(self.M)

    def as_euler_xyz(self):
        """ 
        Return the euler angles in degrees.  No error checking.
        P 322,602 of Graphics Gems II
        """
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

    def as_euler_zyx(self):
        """ 
        Return the euler angles in degrees.  No error checking.
        P 322,602 of Graphics Gems II
        """
        b = math.asin(self.M[2][0])
        Cb = math.cos(b)
        nz = math.isclose(Cb,0.0, abs_tol = 1e-09)
        nz21 = math.isclose(self.M[2][1],0.0, abs_tol = 1e-09)
        nz22 = math.isclose(self.M[2][2],0.0, abs_tol = 1e-09)
        if (Cb == 0.0) or (nz and nz21 and nz22):
            a = math.atan2(-self.M[0][1], self.M[1][1])
            c = 0.0
        else:
            a = math.atan2(-self.M[2][1], self.M[2][2])
            c = math.atan2(-self.M[1][0], self.M[0][0])

        return np.array([math.degrees(a), math.degrees(b), math.degrees(c)])

    def as_euler_yzx(self):
        """ 
        Extract Y first to get full -180 to 180
        Return the euler angles in degrees.  No error checking.
        """
        c = math.asin(-self.M[2][0])

        if (math.cos(c) != 0.0) :
            a = math.atan2(self.M[1][2], self.M[1][1])
            b = math.atan2(self.M[2][0], self.M[0][0])
        else:
            a = math.atan2(self.M[2][1], self.M[2][2])
            b = 0.0

        return np.array([math.degrees(a), math.degrees(b), math.degrees(c)])
    def as_euler_xzy(self):
        """ 
        Extract Y last to get full -180 to 180
        Return the euler angles in degrees.  No error checking.
        """
        c = math.asin(self.M[0][1])

        if (math.cos(c) != 0.0) :
            a = math.atan2(-self.M[2][1], self.M[1][1])
            b = math.atan2(-self.M[0][2], self.M[0][0])
        else:
            a = math.atan2(self.M[1][2], self.M[2][2])
            b = 0.0

        return np.array([math.degrees(a), math.degrees(b), math.degrees(c)])

    def as_euler(self, order:str):
        if order == "xyz":
            return self.as_euler_xyz()
        if order == "zyx":
            return self.as_euler_zyx()
        if order == "yzx":
            return self.as_euler_yzx()
        if order == "xzy":
            return self.as_euler_xzy()

        print(f"Don't know that rotation order yet.")
        return np.array([0.0,0.0,0.0])

    def as_axis_angle(self):
        """ Return the (axis, angle) tuple of the rotation. Angle in degrees"""
        axis = np.array([0.0,0.0,0.0])
        c = (self.M[0][0] + self.M[1][1] + self.M[2][2] - 1.0)/2.0
        angle = math.acos(c)
        s = math.sin(angle)
        if s == 0.0:
            # angle is zero, axis doesn't matter
            axis[0] = 1
        else:
            axis[0] = (self.M[1][2] - self.M[2][1])/(2.0*s)
            axis[1] = (self.M[2][0] - self.M[0][2])/(2.0*s)
            axis[2] = (self.M[0][1] - self.M[1][0])/(2.0*s)
        return (axis, math.degrees(angle))

    def as_quat(self):
        ww = 0.25 * ( 1.0 + self.M[0][0] + self.M[1][1] + self.M[2][2])
        if ww > sys.float_info.epsilon:
            w = math.sqrt(ww)
            div_w = 1.0/(4.0 * w)
            x = (self.M[1][2] - self.M[2][1]) * div_w
            y = (self.M[2][0] - self.M[0][2]) * div_w
            z = (self.M[0][1] - self.M[1][0]) * div_w
        else:
            w = 0.0
            xx = -0.5 * (self.M[1][1] + self.M[2][2])
            if xx > sys.float_info.epsilon:
                x = math.sqrt(xx)
                y = self.M[0][1] / (2.0 * x)
                z = self.M[0][2] / (2.0 * x)
            else:
                x = 0.0
                yy = 0.5 * (1.0 - self.M[2][2])
                if yy > sys.float_info.epsilon:
                    y = math.sqrt(yy)
                    z = self.M[1][2]/(2.0*y)
                else:
                    y = 0.0
                    z = 1.0
        return np.array([x,y,z,w])


def normalize(n):
    l = np.linalg.norm(n)
    return n/l

def run_tests():
    """
    Compare/validate results with scipy
    """
    import scipy
    import random

    # Euler angle test
    e = np.array([0.0,0.0,0.0])
    e[0] = random.uniform(-360.0,360.0)
    e[1] = random.uniform(-360.0,360.0)
    e[2] = random.uniform(-360.0,360.0)
    print(f"Euler rotation is {e}")
    M = QRotation.from_euler("xyz",e)
    print(f"M is {M}")
    R = scipy.spatial.transform.Rotation.from_euler("xyz",e, degrees=True)
    print(f"R.inv() is \n{R.inv().as_matrix()}")

    # axis-angle/rotvec test
    a = np.array([0.0,0.0,0.0])
    a[0] = random.uniform(-1.0,1.0)
    a[1] = random.uniform(-1.0,1.0)
    a[2] = random.uniform(-1.0,1.0) 
    a = normalize(a) 
    theta = math.radians(random.uniform(-180.0,180.0))
    M = QRotation.from_axis_angle(a,theta)
    R = scipy.spatial.transform.Rotation.from_rotvec(a * theta)
    print(f"Axis Angle is {a} {theta}")
    print(f"M is {M}")
    print(f"R.inv() is \n{R.inv().as_matrix()}")

    q = M.as_quat()
    N = QRotation.from_quat(q)
    print(f"Quat is {q}")
    print(f"Rot from Quat is {N}")


#print(f"__name__ is {__name__}")
#print(f"__file__ is {__file__}")
if __name__ == "__main__":
    run_tests()

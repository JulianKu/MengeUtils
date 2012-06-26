import numpy as np

AGENTRADIUS = 1.0
LAMBDA = 1.  # smoothing parameter in variable Gaussian
LAMBDA_SQRD = LAMBDA * LAMBDA

# Functions to estimate density used in Kernel class
def uniformFunc( dispX, dispY, radius ):
    """ Density Estimation using uniform function -> square in 2D """
    maskX = dispX <= radius
    maskY = dispY <= radius
    maskXY = maskX & maskY
    return maskXY/2.

def linearFunc( dispX, dispY, radius):
    """ Density Esitmation using linear function -> cone in 2D """
    distXY = np.sqrt( dispX * dispX + dispY * dispY )
    maskXY = distXY <= radius
    valueXY = (1 - distXY) * maskXY
    ## For testing by ploting gradient or value of the function
    ## gradX, gradY = np.gradient(valueXY)
    ## gradMag = np.sqrt( gradX * gradX + gradY * gradY )
    ## plt.contour( valueXY )
    ## plt.axis('equal')
    ## plt.show()
    return valueXY

def biweightFunc( dispX, dispY, radius):
    rSqd = radius * radius
    dispYSqd = dispY * dispY
    distXY = dispX * dispX + dispYSqd
    maskXY = np.sqrt(distXY) <= radius
    valueXY = -( distXY )/rSqd
    valueXY += 1
    # Normalize the biweight function
    valueXY /= (4. * rSqd)/ 3.
    valueXY *= maskXY
    ## For testing by ploting gradient or value of the function
    ## gradX, gradY = np.gradient( valueXY )
    ## gradMag = np.sqrt( gradX * gradX + gradY * gradY )
    ## plt.contour( valueXY )
    ## plt.axis( 'equal' )
    ## plt.show()
    return valueXY
        
def gaussianFunc( dispX, dispY, radiusSqd ):
    """ Density Estimation  using gaussian function """
    return np.exp( -(dispX * dispX + dispY * dispY) / (2.0 * radiusSqd ) ) / ( 2.0 * np.pi * radiusSqd )

def variableGaussianFunc( dispX, dispY, radiusSqd ):
    """ Density Estimation  using gaussian function with varied radius"""
    # Have to be seperated from normal Gaussian for function pointer testing in Kernel and Grid file
    return np.exp( -(dispX * dispX + dispY * dispY) / (2.0 * radiusSqd * LAMBDA_SQRD ) ) / ( 2.0 * np.pi *
                                                                               radiusSqd * LAMBDA_SQRD )

UNIFORM = lambda X, Y, R: uniformFunc( X, Y, R ) 
GAUSS   = lambda X, Y, R: gaussianFunc( X, Y, R * R )
LINEAR  = lambda X, Y, R: linearFunc( X, Y, R )
BIWEIGHT = lambda X, Y,R: biweightFunc( X, Y, R )
VARGAUSS = lambda X, Y,R: variableGaussianFunc( X, Y, R * R)

FUNC_MAPS = { "uniform": UNIFORM,
              "gaussian": GAUSS,
              "variable-gaussian":VARGAUSS,
              "linear": LINEAR,
              "biweight": BIWEIGHT
              }
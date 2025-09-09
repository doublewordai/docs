import Slider from 'react-infinite-logo-slider';

function MySlider({children}) {
  const borderColor = 'var(--ifm-background-color)';
  const textColor = 'var(--ifm-font-color-base)'

  return (
      <div>
        <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
        >
          <div
              style={{
                boxSizing: 'border-box',
                fontSize: 0,
                textAlign: 'center',
                color: textColor,
              }}
          >
            <div
                style={{
                  display: 'inline-block',
                  fontSize: '12px',
                  fontFamily: 'Helvetica',
                  color: textColor,
                  lineHeight: 1.2,
                  pointerEvents: 'all',
                  whiteSpace: 'normal',
                  wordWrap: 'normal',
                }}
            >
            </div>
          </div>
        </div>

        <Slider
            width="150px"
            duration={15}
            pauseOnHover
            blurBorders
            blurBorderColor={borderColor}
            id="slide"
        >
          {children}
        </Slider>
      </div>

      );
}

export default MySlider;
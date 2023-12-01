import React, { useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Text, Box, useMantineTheme } from '@mantine/core';
import Mercedes from '../assets/mercedes.svg';
import { motion, AnimatePresence } from 'framer-motion';
import { getDatabase, ref, onValue } from '../firebase'; // Removed unused 'get' import

// ... (기존 import문들)

// 주차 데이터를 가져오는 비동기 함수
const fetchParkingData = async () => {
  const db = getDatabase();
  const response = await ref(db, 'parking_spot_state').get(); 
  return response.val();
};

function ParkingSpot() {
  const queryClient = useQueryClient();
  const { data: parkingData, isLoading } = useQuery({
    queryKey: '[parkingData]',
    queryFn: fetchParkingData,
  });
  const theme = useMantineTheme();
  const [reg1, setReg1] = React.useState(false); // A1 주차 공간의 등록 상태
  const [reg2, setReg2] = React.useState(false); // A2 주차 공간의 등록 상태

  useEffect(() => {
    const db = getDatabase();
    
    // A1 주차 공간 등록 상태 가져오기
    const reg1Ref = ref(db, 'parking_spot_registered/A1');
    onValue(reg1Ref, (snapshot) => {
      setReg1(snapshot.val());
    });

    // A2 주차 공간 등록 상태 가져오기
    const reg2Ref = ref(db, 'parking_spot_registered/A2');
    onValue(reg2Ref, (snapshot) => {
      setReg2(snapshot.val());
    });

    // 주차 데이터 변경 시 쿼리 데이터 업데이트
    const docRef = ref(db, 'parking_spot_state');
    const unsubscribe = onValue(docRef, (snapshot) => {
      queryClient.setQueryData('[parkingData]', snapshot.val());
    });

    return () => unsubscribe();
  }, [queryClient]);

  return (
    // 주차 공간 상태를 나타내는 컴포넌트
    <Box component="div" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <Text>Parking Spot Status</Text>
      {isLoading && <p>Loading...</p>}
      {parkingData && (
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          {Object.entries(parkingData).map(([spotName, status]) => (
            <div key={spotName} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginRight: '20px' }}>
              {/* 각 주차 공간을 나타내는 박스 */}
              <Box
                key={spotName}
                component="div"
                style={{
                  borderBottom: '1px solid',
                  borderColor: theme.colors.gray[1],
                  width: '120px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  alignItems: spotName === 'A1' ? 'flex-start' : 'flex-end',
                  height: 100,
                  position: 'relative',
                  backgroundColor: (status === true && spotName === 'A1' && reg1) || (status === true && spotName === 'A2' && reg2) ? 'green' : (status === false ? 'white' : 'red'),
                }}
              >
                {/* 주차 공간이 차지된 경우 애니메이션과 함께 차 이미지 표시 */}
                <AnimatePresence>
                  {status === true && (
                    <motion.div
                      key={`${spotName}-motion`}
                      initial={{ x: 0, opacity: 0 }}
                      animate={{ x: spotName === 'A2' ? -20 : 20, opacity: 1 }}
                      exit={{ x: 0, opacity: 0 }}
                      transition={{ duration: 1, type: 'spring', damping: '10' }}
                      style={{
                        position: 'relative',
                        left: spotName === 'A2' ? undefined : -40,
                        right: spotName === 'A2' ? -40 : undefined,
                        alignItems: 'center',
                      }}
                    >
                      {/* 차 이미지 표시 */}
                      <img
                        src={Mercedes}
                        height={60}
                        alt="mercedes car top view"
                        style={{
                          transform: spotName === 'A1' ? undefined : 'rotate(180deg)',
                          filter: `drop-shadow(0px 3px 3px rgba(0, 0, 0, 0.4)`,
                        }}
                      />
                    </motion.div>
                  )}
                </AnimatePresence>
                {/* 주차 공간이 비어있는 경우 'Available' 텍스트 표시 */}
                {status === false && (
                  <Text
                    style={{
                      position: 'absolute',
                      top: '50%',
                      left: '50%',
                      transform: 'translate(-50%, -50%)',
                      color: theme.colors.gray[9],
                    }}
                  >
                    Available
                  </Text>
                )}
                {/* 주차 공간 이름 표시 */}
                <Text
                  fz="sm"
                  style={{
                    position: 'absolute',
                    bottom: -5,
                    left: spotName === 'A2' ? undefined : 0,
                    right: spotName === 'A2' ? 0 : undefined,
                    color: theme.colors.gray[6],
                  }}
                >
                  {spotName}
                </Text>
              </Box>
              {/* "등록차량" 또는 "비등록차량" 표시 */}
              <div style={{ marginTop: '5px', backgroundColor: (status === true && spotName === 'A1' && reg1) || (status === true && spotName === 'A2' && reg2) ? 'green' : (status === false ? 'white' : 'red'), color: 'white', padding: '5px', borderRadius: '5px' }}>
                {status === true && (spotName === 'A1' ? reg1 : reg2) ? '등록차량' : '비등록차량'}
              </div>
            </div>
          ))}
        </div>
      )}
    </Box>
  );
}

export default ParkingSpot;

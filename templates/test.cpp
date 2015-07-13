//google test docs
//wiki page: https://code.google.com/p/googletest/w/list
//primer: https://code.google.com/p/googletest/wiki/V1_7_Primer
//FAQ: https://code.google.com/p/googletest/wiki/FAQ
//advanced guide: https://code.google.com/p/googletest/wiki/V1_7_AdvancedGuide
//samples: https://code.google.com/p/googletest/wiki/V1_7_Samples

//List of some basic tests:
//Fatal assertion                      Nonfatal assertion                   Verifies
//-------------------------------------------------------------------------------------------------------------------------------------------------------
//ASSERT_EQ(expected, actual);         EXPECT_EQ(expected, actual);         expected == actual
//ASSERT_NE(val1, val2);               EXPECT_NE(val1, val2);               val1 != val2
//ASSERT_LT(val1, val2);               EXPECT_LT(val1, val2);               val1 < val2
//ASSERT_LE(val1, val2);               EXPECT_LE(val1, val2);               val1 <= val2
//ASSERT_GT(val1, val2);               EXPECT_GT(val1, val2);               val1 > val2
//ASSERT_GE(val1, val2);               EXPECT_GE(val1, val2);               val1 >= val2
//
//ASSERT_FLOAT_EQ(expected, actual);   EXPECT_FLOAT_EQ(expected, actual);   the two float values are almost equal (4 ULPs)
//ASSERT_DOUBLE_EQ(expected, actual);  EXPECT_DOUBLE_EQ(expected, actual);  the two double values are almost equal (4 ULPs)
//ASSERT_NEAR(val1, val2, abs_error);  EXPECT_NEAR(val1, val2, abs_error);  the difference between val1 and val2 doesn't exceed the given absolute error
//
//Note: more information about ULPs can be found here: http://www.cygnus-software.com/papers/comparingfloats/comparingfloats.htm

#include "gtest/gtest.h"

//A google test function (uncomment the next function
//TODO: Change TestGroup and TestName to a appropriate name
//TEST(TestGroup, TestName) {
	//TODO: Add your test code here
//}

int main(int argc, char **argv) {
	::testing::InitGoogleTest(&argc, argv);
	return RUN_ALL_TESTS();
}


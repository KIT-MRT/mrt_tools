#include "${class_name}.hpp"

int main(int argc, char* argv[]) {

    ros::init(argc, argv, "${class_name}_node");

    ${pkgname}::${ClassName} converter(ros::NodeHandle(), ros::NodeHandle("~"));

    ros::spin();
    return 0;
}